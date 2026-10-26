"""Precision corruption tests; native execution remains a separate explicit gate."""
import json
import subprocess
import struct
import tempfile
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
from protocol import ProtocolError
from state_trace import float_transport as codec
from state_trace import native_capture


def wire():
    values = [repr(codec.from_bits(bits)) + '|' + str(bits) for bits in codec.BITS]
    payload = dict(text='Gaia\'s "Landing"\\road\nline\ttab', value=codec.from_bits(codec.BITS[3]),
                   signed_zero=-0.0, integer=1, boolean=True, empty=None)
    return '\n'.join(['FLOAT_CODEC|' + value for value in values] +
                     ['TRACE_CODEC_JSON|' + json.dumps(payload), 'BEHAVIOR_SUMMARY 2 16', 'All tests passed.'])


class PrecisionTests(unittest.TestCase):
    def test_exact_independent_native_bit_values_and_json_escapes(self):
        report = codec.audit(wire())
        self.assertEqual(report['sample_count'], 8)
        self.assertTrue(report['signed_zero_preserved'])
        self.assertEqual(report['payload']['value'], 0.3333333432674408)

    def test_nine_digits_that_roundtrip_f32_still_fail_strict_json_value(self):
        native = codec.from_bits(codec.BITS[3])
        rounded = 0.333333343
        self.assertEqual(codec.BITS[3], struct.unpack('>I', struct.pack('>f', rounded))[0])
        self.assertNotEqual(native, rounded)
        with self.assertRaises(ProtocolError): codec.audit(wire().replace(repr(native) + '|', str(rounded) + '|', 1))

    def test_six_digits_nonfinite_integer_type_and_signed_zero_corruption_fail(self):
        original = wire()
        cases = [original.replace('0.3333333432674408|', '0.333333|', 1),
                 original.replace('0.3333333432674408|', 'NaN|', 1),
                 original.replace('1.0|1065353216', '1|1065353216'),
                 original.replace('-0.0|2147483648', '0.0|2147483648')]
        for value in cases:
            with self.subTest(value=value[:80]), self.assertRaises(ProtocolError): codec.audit(value)

    def test_missing_duplicate_reordered_native_fields_and_bad_summary_fail(self):
        original = wire()
        lines = original.splitlines()
        cases = ['\n'.join(lines[1:]), original + '\n' + lines[0],
                 '\n'.join([lines[1], lines[0]] + lines[2:]),
                 original.replace('All tests passed.', 'TEST FAILED'),
                 original.replace('"integer": 1', '"integer": 1.0')]
        for value in cases:
            with self.subTest(value=value[:80]), self.assertRaises(ProtocolError): codec.audit(value)

    def test_native_timeout_and_spawn_failure_have_distinct_execution_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / 'GLSMAC.js'; runtime.write_text('loader')
            runtime.with_suffix('.wasm').write_bytes(b'wasm')
            process = MagicMock(); process.__enter__.return_value = process
            process.communicate.side_effect = [subprocess.TimeoutExpired('node', 1), ('BEHAVIOR_BEGIN native\n', '')]
            with patch.object(native_capture.subprocess, 'Popen', return_value=process), self.assertRaises(native_capture.NativeCaptureError) as caught:
                native_capture.capture_script(runtime, codec.SCRIPT, timeout=1)
            self.assertTrue(caught.exception.execution['candidate_executed'])
            self.assertTrue(caught.exception.execution['native_execution_confirmed'])
            process.kill.assert_called_once(); self.assertEqual(process.communicate.call_count, 2)
            with patch.object(native_capture.subprocess, 'Popen', side_effect=FileNotFoundError('node')), self.assertRaises(native_capture.NativeCaptureError) as caught:
                native_capture.capture_script(runtime, codec.SCRIPT)
            self.assertFalse(caught.exception.execution['candidate_executed'])
            self.assertFalse(caught.exception.execution['native_execution_confirmed'])


if __name__ == '__main__': unittest.main()
