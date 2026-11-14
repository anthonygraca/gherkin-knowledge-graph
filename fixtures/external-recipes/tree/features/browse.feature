@browse
Feature: Recipe browsing
  A visitor browses the public catalog without signing in.

  Background:
    Given the catalog contains "Soup" and "Stew"

  Rule: Only published recipes are visible

    Scenario: Published recipes are listed
      When the visitor opens the catalog
      Then the catalog shows "Soup"
      And the catalog shows "Stew"

    @SCN-001
    Scenario: Draft recipes stay hidden
      Given a draft recipe "Pie"
      When the visitor opens the catalog
      Then the catalog does not show "Pie"

  Scenario Outline: Search by <term>
    When the visitor searches for "<term>"
    Then the result list is "<verdict>"
    And the visitor sees the search note
      """
      query: <term>
      """
    And the search filters include
      | filter | value  |
      | term   | <term> |
    And the search does not require an account

    Examples:
      | term  | verdict |
      | soup  | Hits    |
      | toast | Empty   |
