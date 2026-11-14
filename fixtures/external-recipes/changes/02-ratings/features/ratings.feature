Feature: Recipe ratings
  Scenario: A visitor rates a recipe once
    Given a published recipe "Soup"
    When the visitor rates it 5
    Then the recipe shows an average rating of 5
    And a second rating by the same visitor replaces the first
