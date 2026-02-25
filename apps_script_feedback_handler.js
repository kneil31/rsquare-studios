// ── Add this block to the EXISTING doPost(e) function ──
// Insert BEFORE the existing video_project and review handlers.
//
// After adding, deploy as NEW VERSION:
//   Extensions → Apps Script → Deploy → New deployment → Web app → Anyone
//   IMPORTANT: Must select "New version" when redeploying, or old code runs.
//
// Google Sheet setup:
//   1. Add a new tab called "Feedback" to the existing Sheet
//   2. Add headers in row 1: Project | Type | Timestamp | Content | Priority | Submitted | PIN
//   3. Copy the tab's GID from the URL (?gid=XXXXXXX) into sheets_sync.py GID_FEEDBACK

// ── Inside doPost(e) — add this block: ──

  var data = e.parameter;
  var type = data.type || "";

  if (type === "feedback") {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("Feedback");
    if (!sheet) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "error",
        message: "Feedback tab not found"
      })).setMimeType(ContentService.MimeType.JSON);
    }
    sheet.appendRow([
      data.project || "",
      data.feedback_type || "",
      data.timestamp || "",
      data.content || "",
      data.priority || "",
      new Date(),
      data.pin || ""
    ]);
    return ContentService.createTextOutput(JSON.stringify({
      status: "ok",
      message: "Feedback saved"
    })).setMimeType(ContentService.MimeType.JSON);
  }

// ── Keep existing video_project and review handlers below ──
