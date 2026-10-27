const behavior = #include('./_behavior'); const scenarios = #include('./_unit_disband_regression_cases');
// Each existing case creates and removes its own UI/native fixture. Execute
// the unchanged body at a top-level staging boundary so its temporary world
// observations can be collected before the next independent case begins.
for (let index = 0; index < 7; index++) {
	const entry = scenarios[index]; const step = {label: 'existing-case'}; step.run = entry.run;
	const steps = []; steps :+ step; behavior.scenario_staged(entry.name, steps);
}
