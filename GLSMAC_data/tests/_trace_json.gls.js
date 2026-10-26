// Strict detached-data transport only. Native wrappers/functions/undefined are
// rejected instead of silently omitted. Python validates the resulting JSON.
const replace = (text, separator, replacement) => {
 let result = ''; let first = true;
 for (part of #split(text, separator)) { if (!first) { result += replacement; } result += part; first = false; }
 return result;
};
const quoted = (text) => {
 let value = replace(text, '\\', '\\\\');
 value = replace(value, '"', '\\"');
 value = replace(value, '\n', '\\n');
 value = replace(value, '\r', '\\r');
 value = replace(value, '\t', '\\t');
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
