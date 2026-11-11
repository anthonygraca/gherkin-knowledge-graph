Feature: Transfers

  @SCN-002
  Scenario: Transfer above the daily limit is rejected
    Given a transfer ledger with a daily limit of 1000.00 dollars
    When a transfer of 1200.00 dollars is requested
    Then the transfer is rejected with a daily limit error
    And the ledger records no transfer entry

  @SCN-003
  Scenario: Transfer of exactly the daily limit is permitted
    Given a transfer ledger with a daily limit of 1000.00 dollars
    When a transfer of 1000.00 dollars is requested
    Then the transfer is recorded
    And the daily transferred total is 1000.00 dollars
