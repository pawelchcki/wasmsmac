#!/usr/bin/env python3
"""Strict JSON value/zero-sign audit against independently exported native f32 bits."""
import argparse
import json
import math
from pathlib import Path
import re
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fast import parse_output
from protocol import ProtocolError, canonical, decode_json
from state_trace.native_capture import ROOT, NativeCaptureError, capture_script

SCRIPT = ROOT / 'GLSMAC_data/tests/trace_float_transport.gls.js'
# Independent authored sample inputs, including signed zero; not reference gold.
SAMPLES = (0.0, -0.0, 1.0, 1.0 / 3.0, 0.1, 1e-20, 1e20, -1.0 / 3.0)
BITS = tuple(struct.unpack('>I', struct.pack('>f', value))[0] for value in SAMPLES)


def from_bits(bits):
    return struct.unpack('>f', struct.pack('>I', bits))[0]


def exact(value, native):
    return (type(value) is float and math.isfinite(value) and value == native
            and (value != 0.0 or math.copysign(1, value) == math.copysign(1, native)))


def audit(log):
    parse_output(log)
    samples, payloads = [], []
    for line in log.splitlines():
        match = re.search(r'(?:^|\] )(FLOAT_CODEC|TRACE_CODEC_JSON)\|(.*)$', line)
        if not match:
            continue
        kind, body = match.groups()
        if kind == 'TRACE_CODEC_JSON':
            payloads.append(decode_json(body))
        else:
            fields = body.split('|')
            if len(fields) != 2:
                raise ProtocolError('Malformed native float sample')
            try:
                bits = int(fields[1])
                if not 0 <= bits <= 0xffffffff:
                    raise ValueError('bits out of range')
                value = decode_json(fields[0])
            except (ValueError, OverflowError) as error:
                raise ProtocolError('Malformed native float value/bits') from error
            if not exact(value, from_bits(bits)):
                raise ProtocolError('JSON number differs from the actual promoted native binary32 value')
            samples.append(bits)
    if tuple(samples) != BITS or len(payloads) != 1:
        raise ProtocolError('Missing/duplicate/reordered native float samples or JSON payload')
    payload = payloads[0]
    expected = {'text': 'Gaia\'s "Landing"\\road\nline\ttab', 'integer': 1, 'boolean': True, 'empty': None}
    if type(payload) is not dict or set(payload) != set(expected) | {'value', 'signed_zero'}:
        raise ProtocolError('Native detached JSON fields missing')
    if any(type(payload[k]) is not type(v) or payload[k] != v for k, v in expected.items()):
        raise ProtocolError('Native JSON text/integer/boolean/null transport changed')
    if not exact(payload['value'], from_bits(BITS[3])) or not exact(payload['signed_zero'], -0.0):
        raise ProtocolError('Native JSON float precision or signed zero changed')
    return dict(sample_count=len(samples), strict_json_native_value_equal=True,
                signed_zero_preserved=True, payload=payload)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--runtime', type=Path)
    group.add_argument('--log', type=Path, help='validate captured bytes only; does not execute candidate')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    report = dict(candidate_executed=False, validation_only=bool(args.log))
    try:
        if args.runtime:
            log, execution = capture_script(args.runtime, SCRIPT)
            report.update(candidate_executed=True, execution=execution)
        else:
            log = args.log.read_text()
        report.update(status='passed', audit=audit(log))
        code = 0
    except NativeCaptureError as error:
        report.update(status='error', candidate_executed=error.execution['candidate_executed'],
                      execution=error.execution, error=str(error), native_log=error.log)
        code = 2
    except (OSError, ValueError, ProtocolError) as error:
        report.update(status='error', error=str(error))
        code = 2
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + '\n')
    print(canonical(report))
    return code


if __name__ == '__main__':
    sys.exit(main())
