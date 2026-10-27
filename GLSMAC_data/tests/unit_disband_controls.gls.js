const behavior = #include('./_behavior'); const scenarios = #include('./_unit_disband_regression_cases');
// Original seven independent bodies and their cleanup remain unchanged.
// Group only the empty bookkeeping stages, never the genuine case boundaries.
const cases = [];
for (let index = 0; index < 7; index++) { cases :+ scenarios[index]; }
behavior.group_staged(cases);
