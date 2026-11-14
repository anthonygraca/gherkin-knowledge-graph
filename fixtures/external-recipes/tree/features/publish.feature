@authoring
Feature: Recipe authoring
  Scenario: Publishing a recipe requires a title
    Given an author with a draft recipe
    When the author publishes it without a title
    Then publication is rejected with "title is required"
