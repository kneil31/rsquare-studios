// ── Add this block to the EXISTING doPost(e) function ──
// Insert BEFORE the existing video_project and review handlers.
//
// After adding, deploy as NEW VERSION:
//   Extensions → Apps Script → Deploy → New deployment → Web app → Anyone
//   IMPORTANT: Must select "New version" when redeploying, or old code runs.
//
// Google Sheet setup:
//   1. Add a new tab called "Feedback" to the existing Sheet
//   2. Add headers in row 1: Project | Type | Timestamp | Content | Priority | Submitted | PIN | Fixed
//   3. Copy the tab's GID from the URL (?gid=XXXXXXX) into sheets_sync.py GID_FEEDBACK
//
// Email notifications:
//   - When client submits correction → email editor + Ram
//   - When editor marks as fixed → email Ram
//   UPDATE these email addresses before deploying:

var FEEDBACK_EMAIL_RAM = "YOUR_EMAIL_HERE";       // Replace with actual email before deploying
var FEEDBACK_EMAIL_EDITOR = "editor@example.com";           // TODO: Replace with Madhu's actual email

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
      data.pin || "",
      ""  // Fixed column (empty on new submissions)
    ]);

    // Email notification — client submitted feedback
    try {
      var feedbackType = data.feedback_type || "feedback";
      var subject = "[Rsquare] " + (data.project || "Unknown") + " — New " + feedbackType;
      var body = "Project: " + (data.project || "Unknown") + "\n" +
                 "Type: " + feedbackType + "\n";
      if (data.timestamp) body += "Timestamp: " + data.timestamp + "\n";
      body += "Content: " + (data.content || "") + "\n";
      if (data.priority) body += "Priority: " + data.priority + "\n";
      body += "\nSubmitted: " + new Date().toLocaleString() + "\n";
      body += "\nView all feedback: https://portfolio.rsquarestudios.com/feedback/?role=editor";

      MailApp.sendEmail({
        to: FEEDBACK_EMAIL_EDITOR,
        cc: FEEDBACK_EMAIL_RAM,
        subject: subject,
        body: body,
      });
    } catch(emailErr) {
      // Don't fail the request if email fails
      Logger.log("Email send failed: " + emailErr);
    }

    return ContentService.createTextOutput(JSON.stringify({
      status: "ok",
      message: "Feedback saved"
    })).setMimeType(ContentService.MimeType.JSON);
  }

  // ── Feedback Update (editor marks correction as fixed/unfixed) ──

  if (type === "feedback_update") {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("Feedback");
    if (!sheet) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "error",
        message: "Feedback tab not found"
      })).setMimeType(ContentService.MimeType.JSON);
    }
    var rows = sheet.getDataRange().getValues();
    var found = false;
    for (var i = 1; i < rows.length; i++) {
      // Match by Project (col A) + Timestamp (col C) + Content (col D)
      if (rows[i][0] == data.project &&
          rows[i][2] == data.timestamp &&
          rows[i][3] == data.content) {
        // Column H = "Fixed" (index 7, getRange is 1-based so col 8)
        var isFixed = data.fixed === "yes";
        sheet.getRange(i + 1, 8).setValue(isFixed ? "yes" : "");
        found = true;

        // Email Ram when editor marks a correction as fixed
        if (isFixed) {
          try {
            var fixSubject = "[Rsquare] " + (data.project || "Unknown") + " — Correction fixed";
            var fixBody = "Project: " + (data.project || "Unknown") + "\n";
            if (data.timestamp) fixBody += "Timestamp: " + data.timestamp + "\n";
            fixBody += "Correction: " + (data.content || "") + "\n";
            fixBody += "\nMarked as fixed by editor at " + new Date().toLocaleString() + "\n";
            fixBody += "\nView all: https://portfolio.rsquarestudios.com/feedback/?role=editor";

            MailApp.sendEmail({
              to: FEEDBACK_EMAIL_RAM,
              subject: fixSubject,
              body: fixBody,
            });
          } catch(emailErr) {
            Logger.log("Email send failed: " + emailErr);
          }
        }

        break;
      }
    }
    return ContentService.createTextOutput(JSON.stringify({
      status: found ? "ok" : "not_found",
      message: found ? "Fixed status updated" : "Correction row not found"
    })).setMimeType(ContentService.MimeType.JSON);
  }

// ── Keep existing video_project and review handlers below ──
