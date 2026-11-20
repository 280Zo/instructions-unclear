# Azure DevOps, Agile process

Each entry was checked against the source linked under it.

## Work item types and hierarchy

The Agile process uses Epic, Feature, User Story and Task, plus Issue, Bug and Test Case. User stories map to features, and teams break stories into tasks: Epic, then Feature, then User Story, then Task. The Scrum process calls the story level Product Backlog Item, and CMMI calls it Requirement.

Sources: https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/agile-process-workflow?view=azure-devops, https://learn.microsoft.com/en-us/azure/devops/boards/queries/import-work-items-from-csv?view=azure-devops

## User story fields

- Title.
- Description: who the story is for, what they want to accomplish, and why. Don't describe how to build it.
- Acceptance Criteria: a separate field for what must be true before the story can be closed. It's the basis for acceptance tests.
- Story Points, Priority, Value Area: planning fields, usually filled in by the team.
- Area Path, Iteration Path, Tags: where the item lives and how it's labeled.

Source: https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/agile-process-workflow?view=azure-devops

## Markdown or HTML in text fields

Large text fields (Description, Acceptance Criteria) use the HTML editor by default. Since July 2025, a field can be switched to Markdown, and the switch can't be undone. Markdown pasted into a field in Markdown mode renders as written. HTML pasted into Markdown mode is converted on a best-effort basis. HTML is the default until a user picks Markdown for a new item. After that, their new items default to Markdown. Pasted Markdown renders as formatted text only in a field that's in Markdown mode, so switch the field to Markdown before pasting.

Source: https://devblogs.microsoft.com/devops/markdown-support-arrives-for-work-items/

## Bulk import from CSV

- New work items need the `Work Item Type` and `Title` columns. Leave out the `ID` column when every row is new.
- To put new items under an existing item, add an `ID` column. Give the existing item its row with its ID and title in `Title 1`, then put the new children under it in `Title 2` with their ID left empty. This is the pattern in Microsoft's FAQ example. When the notes don't give the existing item's ID, leave a placeholder such as `<ID of Usage reports>` and list it under Open questions.
- Add parent-child links by indenting the title columns: `Title 1` for the parent, `Title 2` for its children. Microsoft's example shows two levels. A third level (`Title 3`, for Epic, Feature and User Story) follows the same pattern but isn't shown in the docs, so suggest importing a small file first. No other link type can be imported.
- Don't include the `Assigned To`, `Changed Date`, `Created By` or `State` columns. Put an owner named in the notes into the Description instead (`Owner: Ana`).
- Quote text values that contain commas or line breaks; quoting every text value is the simplest way. HTML is the default editor for large text fields, and HTML tags in a CSV field keep their formatting. Write a list in Description as simple HTML: `<ul><li>First</li><li>Second</li></ul>`. Microsoft's example writes each line of a multi-line field as its own paragraph, so write each Gherkin line in Acceptance Criteria as a `<p>`: `<p>Scenario: Link expires</p><p>Given ...</p><p>When ...</p><p>Then ...</p>`.
- A `Tags` column sets tags. The Agile process has no Spike type, so a spike is a `Task` row with `Spike` in `Tags`. Once the header has a `Tags` column, every row needs a value or an empty field for it, so the columns stay aligned.
- Imported items start in the New state.
- Area and Iteration default to the top-level node unless the file sets them.
- Field names differ between processes and organizations. Suggest exporting a few existing items first to copy their exact column names.
- Import from Boards, then Queries, then Import work items.

```csv
Work Item Type,Title 1,Title 2,Title 3,Description,Acceptance Criteria
Epic,Faster checkout,,,"Shoppers finish checkout with less effort.",
Feature,,Saved payment methods,,"Customers store a card so they don't retype it.",
User Story,,,Save a card at checkout,"As a customer, I want to save my card at checkout, so that I don't retype it next time.","<p>Scenario: Save the card</p><p>Given a customer has entered a card at checkout</p><p>When they choose to save it</p><p>Then the card is saved</p><p>Scenario: Offer the saved card</p><p>Given a customer has saved a card</p><p>When they next check out</p><p>Then the saved card is offered</p>"
```

With a spike, add `Tags` as the last header column, an empty last field on every other row, and a row such as `Task,"Compare PDF libraries",,,"<p>...</p><p>Done when:</p><ul><li>...</li></ul>",,Spike`. A task's Done when list goes in its Description.

Source: https://learn.microsoft.com/en-us/azure/devops/boards/queries/import-work-items-from-csv?view=azure-devops

## Tags

Several tags in one Tags value are separated by semicolons, and a tag name can't contain a comma or semicolon.

Sources: https://learn.microsoft.com/en-us/azure/devops/boards/backlogs/office/bulk-add-modify-work-items-excel?view=azure-devops, https://learn.microsoft.com/en-us/azure/devops/boards/queries/add-tags-to-work-items?view=azure-devops
