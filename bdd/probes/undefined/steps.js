import assert from 'node:assert/strict';
import { Given, Then } from '@cucumber/cucumber';

Given('the probe receives the value {int}', function (value) {
  this.probeValue = value;
});

Then('the probe assertion passes', function () {
  assert.equal(this.probeValue * 2, 12);
});
