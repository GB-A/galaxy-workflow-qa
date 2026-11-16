# Tags: priority (@p1), layer (@api / @ui), requirement (@REQ_nnn), test case (@TC_xxx_nnn).
#


Feature: Running a sample workflow from the UI
  As a platform scientist
  I want to launch the workflow, follow its progress and read the results in Galaxy
  So that I do not need the API to do my analysis

  @p1 @ui @REQ_007 @REQ_008 @REQ_009 @REQ_010 @TC_UI_006 @TC_UI_007 @TC_UI_008 @TC_UI_009
  Scenario: A scientist launches reads_qc, follows the run and reads the protein counts
    Given I am signed in to Galaxy
    Then I create new history item called "Upload Data" and save it
    And I upload "reads.tabular" via the UI
    When I import the workflow file "data/workflows/Galaxy-Workflow-Sample_Test_Flow.ga"
    Then the workflow "Sample Test Flow" is visible in My workflows
    When I run the workflow "Sample Test Flow" on "reads.tabular"
    Then the UI confirms that the workflow run has started
    And workflow job progress is visible
    And every workflow output reaches the "ok" state
    And no history item enters the error state
    And the history panel lists the outputs "Filter on dataset, Sort on dataset, Count on dataset"
    When I open the output "Count on dataset" from the history panel
    Then the "Count on dataset" dataset shown in the UI matches the golden file "golden.tabular"
    And I delete the test history and workflow
