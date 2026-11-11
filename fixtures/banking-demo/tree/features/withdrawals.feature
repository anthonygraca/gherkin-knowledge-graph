Feature: Withdrawals

  @SCN-001
  Scenario: Successful instant withdrawal
    Given an account with a balance of 100.00 dollars
    When the customer withdraws 10.50 dollars
    Then the account balance is 89.50 dollars
    And the withdrawal appears in the account history
