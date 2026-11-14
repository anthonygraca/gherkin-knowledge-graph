#!/usr/bin/env node
/**
 * Strict step-resolution gate for the CTA acceptance suite.
 *
 * Cucumber's process exit code is not enough: a suite can pass while a required scenario was
 * skipped or a step resolved ambiguously and was never executed. This gate reads the Cucumber
 * Messages report and fails when:
 *
 *   - the run did not finish successfully;
 *   - any step was reported UNDEFINED, AMBIGUOUS, or PENDING;
 *   - a pickle (concrete scenario case) never started.
 *
 * Usage: node tools/step-resolution.mjs [reports/cucumber-messages.ndjson]
 */
import fs from 'node:fs';
import path from 'node:path';

const reportPath = process.argv[2] || 'reports/cucumber-messages.ndjson';
const config = (await import(`file://${path.resolve('cucumber.mjs')}`)).default;
const excludedTags = new Set(
  [...String(config.tags ?? '').matchAll(/not\s+(@[\w-]+)/g)].map((match) => match[1]),
);
const envelopes = fs
  .readFileSync(reportPath, 'utf8')
  .split('\n')
  .filter((line) => line.trim())
  .map((line) => JSON.parse(line));

const documents = new Map();
const pickles = new Map();
const testCases = new Map();
const startedByCase = new Map();
const results = new Map();
const definitions = new Map();
const finishedCases = new Set();
let runFinished = null;

for (const envelope of envelopes) {
  if (envelope.gherkinDocument) documents.set(envelope.gherkinDocument.uri, envelope.gherkinDocument);
  if (envelope.pickle) pickles.set(envelope.pickle.id, envelope.pickle);
  if (envelope.testCase) testCases.set(envelope.testCase.id, envelope.testCase);
  if (envelope.testCaseStarted) {
    const ids = startedByCase.get(envelope.testCaseStarted.testCaseId) ?? [];
    ids.push(envelope.testCaseStarted.id);
    startedByCase.set(envelope.testCaseStarted.testCaseId, ids);
  }
  if (envelope.stepDefinition) {
    const source = envelope.stepDefinition.sourceReference ?? {};
    definitions.set(envelope.stepDefinition.id, {
      pattern: envelope.stepDefinition.pattern?.source,
      where: `${source.uri ?? '?'}:${source.location?.line ?? '?'}`,
    });
  }
  if (envelope.testCaseFinished) {
    finishedCases.add(envelope.testCaseFinished.testCaseStartedId);
  }
  if (envelope.testStepFinished) {
    const key = `${envelope.testStepFinished.testCaseStartedId}:${envelope.testStepFinished.testStepId}`;
    const list = results.get(key) ?? [];
    list.push(envelope.testStepFinished.testStepResult);
    results.set(key, list);
  }
  if (envelope.testRunFinished) runFinished = envelope.testRunFinished;
}

function stepLocations(uri) {
  const byId = new Map();
  const walk = (steps) => {
    for (const step of steps ?? []) byId.set(step.id, step.location.line);
  };
  for (const child of documents.get(uri)?.feature?.children ?? []) {
    if (child.background) walk(child.background.steps);
    if (child.scenario) walk(child.scenario.steps);
    for (const sub of child.rule?.children ?? []) {
      if (sub.background) walk(sub.background.steps);
      if (sub.scenario) walk(sub.scenario.steps);
    }
  }
  return byId;
}

const problems = [];
const knownPairs = new Set();
for (const [caseId, testCase] of testCases) {
  for (const attemptId of startedByCase.get(caseId) ?? []) {
    for (const step of testCase.testSteps ?? []) knownPairs.add(`${attemptId}:${step.id}`);
  }
}
for (const key of results.keys()) {
  if (!knownPairs.has(key)) {
    problems.push(`a step result references an unknown attempt or step identity: ${key}`);
  }
}
const anyFailed = [...results.values()].some((list) =>
  list.some((result) => result.status === 'FAILED'),
);
if (runFinished?.success && anyFailed) {
  problems.push('the run reports success but a step result is FAILED');
}
if (!runFinished) problems.push('report has no testRunFinished envelope');
else if (!runFinished.success) problems.push('the run did not finish successfully');
if (testCases.size === 0) problems.push('the report selects no test cases');
if (pickles.size === 0) problems.push('the report contains no pickles');

const coveredPickles = new Set();
for (const [caseId, testCase] of testCases) {
  const pickle = pickles.get(testCase.pickleId);
  if (!pickle) {
    problems.push(`test case ${caseId} references an unknown pickle`);
    continue;
  }
  coveredPickles.add(pickle.id);
  const excluded = (pickle.tags ?? []).some((tag) => excludedTags.has(tag.name));
  if (excluded) continue;
  const attemptIds = startedByCase.get(caseId) ?? [];
  if (attemptIds.length === 0) {
    problems.push(`${pickle.uri}:${pickle.location?.line ?? '?'} "${pickle.name}" never started`);
    continue;
  }
  const locations = stepLocations(pickle.uri);
  const stepsById = new Map((testCase.testSteps ?? []).map((step) => [step.id, step]));
  for (const attemptId of attemptIds) {
    if (!finishedCases.has(attemptId)) {
      problems.push(
        `${pickle.uri}:${pickle.location?.line ?? '?'} "${pickle.name}" attempt ${attemptId} ` +
          'has no testCaseFinished result',
      );
    }
    for (const testStep of testCase.testSteps ?? []) {
      const resultList = results.get(`${attemptId}:${testStep.id}`) ?? [];
      if (resultList.length === 0) {
        problems.push(
          `${pickle.uri}:${pickle.location?.line ?? '?'} "${pickle.name}" has no result for ` +
            `test step ${testStep.id} (incomplete attempt)`,
        );
        continue;
      }
      if (resultList.length > 1) {
        problems.push(
          `${pickle.uri}:${pickle.location?.line ?? '?'} "${pickle.name}" has ` +
            `${resultList.length} results for test step ${testStep.id}`,
        );
      }
      if (!testStep.pickleStepId) {
        const hookStatus = resultList[0].status;
        if (!['PASSED', 'FAILED'].includes(hookStatus)) {
          problems.push(
            `${pickle.uri}:${pickle.location?.line ?? '?'} "${pickle.name}" hook ${testStep.id} ` +
              `is ${hookStatus} [${hookStatus}]`,
          );
        }
        continue;
      }
      const pickleStep = pickle.steps.find((step) => step.id === testStep.pickleStepId);
      if (!pickleStep) continue;
      for (const result of resultList) {
        if (!['UNDEFINED', 'AMBIGUOUS', 'PENDING', 'SKIPPED', 'UNKNOWN'].includes(result.status)) {
          continue;
        }
        const line = locations.get(pickleStep.astNodeIds?.[0]) ?? '?';
        const matched = (testStep.stepDefinitionIds ?? []).map(
          (id) => definitions.get(id)?.where ?? id,
        );
        const detail =
          result.status === 'UNDEFINED'
            ? 'no matching definition'
            : result.status === 'AMBIGUOUS'
              ? `${matched.length} definitions: ${matched.join(', ')}`
              : result.status === 'SKIPPED'
                ? 'was not executed (SKIPPED; dry run or an earlier failure)'
                : result.status === 'PENDING'
                  ? 'is pending'
                  : 'has no result';
        problems.push(
          `${pickle.uri}:${line} "${pickle.name}" step "${pickleStep.text}" ${detail} ` +
            `[${result.status}]`,
        );
      }
    }
  }
}

for (const pickle of pickles.values()) {
  if ((pickle.tags ?? []).some((tag) => excludedTags.has(tag.name))) continue;
  if (!coveredPickles.has(pickle.id)) {
    problems.push(
      `${pickle.uri}:${pickle.location?.line ?? '?'} "${pickle.name}" has no test case ` +
        '(selected scenario omitted from the report)',
    );
  }
}

if (problems.length > 0) {
  console.error('step-resolution: FAILED');
  for (const problem of [...new Set(problems)].sort()) console.error(`  - ${problem}`);
  process.exit(1);
}
console.log(
  `step-resolution: ok (${testCases.size} test cases, ${results.size} step results, all resolved and started)`,
);
