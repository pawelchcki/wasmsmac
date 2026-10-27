// Counts actual native assertions and names scenarios without mocking game rules.
const state = { assertions: 0, scenarios: 0, names: [] };
const native_assert = test.assert;
test.assert = (condition, reason) => {
	state.assertions = state.assertions + 1;
	const message = #typeof(reason) == 'String' ? reason : '';
	native_assert(condition, message);
};

const emit_summary = () => {
 // Older regression scripts contain assertions without named scenarios.
 const scenarios = state.scenarios > 0 ? state.scenarios : 1;
 #print('BEHAVIOR_SUMMARY ' + #to_string(scenarios) + ' ' + #to_string(state.assertions));
};

return {
	scenario: (name, callback) => {
		native_assert(#typeof(name) == 'String' && name != '', 'Scenario requires a name');
		for (previous of state.names) {
			native_assert(previous != name, 'Duplicate scenario: ' + name);
		}
		state.names :+ name;
		#print('BEHAVIOR_BEGIN ' + name);
		callback();
		state.scenarios = state.scenarios + 1;
		#print('BEHAVIOR_PASS ' + name);
	},
 scenario_staged: (name, steps) => {
  native_assert(#typeof(test.stage) == 'Callable' && test.stage_version == 1, 'This test requires native script staging v1');
  native_assert(#typeof(name) == 'String' && name != '' && #typeof(steps) == 'Array', 'Staged scenario requires a name and steps');
  for (previous of state.names) { native_assert(previous != name, 'Duplicate scenario: ' + name); }
  state.names :+ name;
  // This closure owns this case's counters, never an ambient active-case slot.
  const case_state = {started:false,completed:0,expected:#sizeof(steps)};
  test.stage(name + ':begin', () => { case_state.started = true; #print('BEHAVIOR_BEGIN ' + name); });
  let index = 0;
  for (step of steps) {
   native_assert(#typeof(step.label) == 'String' && #typeof(step.run) == 'Callable', 'A staged step requires label/run');
   const callback = step.run; const label = name + ':' + #to_string(index) + ':' + step.label;
   test.stage(label, () => { callback(); case_state.completed = case_state.completed + 1; }); index++;
  }
  test.after_stages(name + ':pass', () => {
   native_assert(case_state.started && case_state.completed == case_state.expected, 'Staged scenario did not complete every declared step');
   state.scenarios = state.scenarios + 1; #print('BEHAVIOR_PASS ' + name);
  });
 },
 finish: () => {
  const has_stages = #typeof(test.stages_pending) == 'Callable' && #typeof(test.after_stages) == 'Callable';
  if (has_stages && test.stages_pending() > 0) { test.after_stages('behavior:summary',emit_summary); }
  else { emit_summary(); }
 },
};
