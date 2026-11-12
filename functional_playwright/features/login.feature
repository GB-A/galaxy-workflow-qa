# Tags: priority (@p1), layer (@api / @ui), requirement (@REQ_nnn), test case (@TC_xxx_nnn).
# See docs/project-structure.md for the tag convention and step vocabulary.

Feature: Signing in to Galaxy
  As a platform scientist
  I want to sign in to Galaxy
  So that I can launch and follow analysis runs

  @p1 @ui @REQ_009 @TC_UI_001
  Scenario: A registered user signs in through the login page
    Given I am not signed in to Galaxy
    When I sign in with the test user credentials
    Then I am taken to the Galaxy home page
    And the user menu shows the test user
