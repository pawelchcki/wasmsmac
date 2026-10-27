const behavior = #include('./_behavior'); const scenarios = #include('./_unit_disband_regression_cases');
// Original seven independent bodies and their cleanup remain unchanged.
// Group only the empty bookkeeping stages, never the genuine case boundaries.
const cases = [];
// Prebind the indexed value: direct push would retain an ArrayRef in GSE.
for (let index = 0; index < 7; index++) { const entry = scenarios[index]; cases :+ entry; }
behavior.group_staged(cases);
