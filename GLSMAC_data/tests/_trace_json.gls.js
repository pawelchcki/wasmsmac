// Strict detached-data transport only. Native wrappers/functions/undefined are
// rejected instead of silently omitted. Python validates the resulting JSON.
const replace = (text, separator, replacement) => {
 // Native split omits a terminal empty segment. Append one separator to
 // preserve it, and reject split's CRLF normalization instead of losing data.
 let result = ''; let restored = ''; let first = true;
 for (part of #split(text + separator, separator)) {
  if (!first) { result += replacement; restored += separator; }
  result += part; restored += part; first = false;
 }
 if (restored != text) { throw Error('Trace string contains unsupported normalized control bytes'); }
 return result;
};
// GSE's lexer treats a quote after ANY backslash as escaped, including an
// even backslash pair. Build the slash from a literal that ends in x instead.
const slash_parts = #split('\\x', 'x'); const slash = slash_parts[0] + '';
const quoted = (text) => {
 let value = replace(text, slash, slash + slash);
 value = replace(value, '"', slash + '"');
 value = replace(value, '\n', slash + 'n');
 value = replace(value, '\t', slash + 't');
 // Other control bytes remain raw and strict JSON decoding rejects them;
 // never reinterpret GSE's unsupported \r escape as the ordinary letter r.
 return '"' + value + '"';
};
const encode = (value) => {
 const type = #typeof(value);
 if (type == 'Null') { return 'null'; }
 if (type == 'String') { return quoted(value); }
 if (type == 'Float') { return #float_text_exact(value); }
 if (type == 'Bool' || type == 'Int') { return #to_string(value); }
 if (type == 'Array') {
  let text = '['; let first = true;
  for (item of value) { if (!first) { text += ','; } text += encode(item); first = false; }
  return text + ']';
 }
 if (type == 'Object') {
  let text = '{'; let first = true;
  for (key in value) { if (!first) { text += ','; } text += quoted(key) + ':' + encode(value[key]); first = false; }
  return text + '}';
 }
 throw Error('Trace requires detached JSON data, got ' + type);
};
return encode;
