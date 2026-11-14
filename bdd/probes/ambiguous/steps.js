import { Given, Then } from '@cucumber/cucumber';

Given('a step that matches twice', function () {
  this.probeValue = 6;
});

Given(/a step that matches tw(?:i|o)ce/, function () {
  this.probeValue = 6;
});

Then('the probe assertion passes', function () {
  this.probeValue = 6;
});
