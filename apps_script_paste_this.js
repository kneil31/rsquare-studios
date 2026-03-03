var FEEDBACK_EMAIL_RAM = "YOUR_EMAIL_HERE";  // Replace with actual email before deploying
var FEEDBACK_EMAIL_EDITOR = "editor@example.com";

function doGet(e) {
  var action = (e.parameter.action || "");
  if (action === "feedback_read") {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("Feedback");
    if (!sheet) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "error", entries: []
      })).setMimeType(ContentService.MimeType.JSON);
    }
    var data = sheet.getDataRange().getValues();
    if (data.length < 2) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "ok", entries: []
      })).setMimeType(ContentService.MimeType.JSON);
    }
    var entries = [];
    for (var i = 1; i < data.length; i++) {
      var row = data[i];
      if (!row[0]) continue;
      // Timestamp: Google Sheets auto-converts "0:45" to Date — extract M:SS
      var tsRaw = row[2];
      var ts = "";
      if (tsRaw) {
        try {
          var d = new Date(tsRaw);
          if (!isNaN(d.getTime())) {
            var h = d.getHours();
            var m = d.getMinutes();
            var s = d.getSeconds();
            if (h > 0) {
              ts = h + ":" + (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
            } else {
              ts = m + ":" + (s < 10 ? "0" : "") + s;
            }
          } else {
            ts = tsRaw.toString();
          }
        } catch(e) {
          ts = tsRaw.toString();
        }
      }
      // Fixed column: "yes", "cant_fix:reason", or empty
      var fixedRaw = (row[7] || "").toString().trim();
      var fixedStatus = "";
      var fixedNote = "";
      if (fixedRaw.toLowerCase() === "yes") {
        fixedStatus = "yes";
      } else if (fixedRaw.toLowerCase().indexOf("cant_fix") === 0) {
        fixedStatus = "cant_fix";
        fixedNote = fixedRaw.substring(fixedRaw.indexOf(":") + 1).trim();
      }
      entries.push({
        project: row[0] || "",
        type: row[1] || "",
        timestamp: ts,
        content: row[3] || "",
        priority: row[4] || "",
        submitted: row[5] ? Utilities.formatDate(row[5], Session.getScriptTimeZone(), "MMM d, h:mm a") : "",
        fixed: fixedStatus,
        fixedNote: fixedNote
      });
    }
    return ContentService.createTextOutput(JSON.stringify({
      status: "ok", entries: entries
    })).setMimeType(ContentService.MimeType.JSON);
  }
  return ContentService.createTextOutput(JSON.stringify({
    status: "error", message: "Unknown action"
  })).setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  var p = e.parameter;
  var type = p.type || "";

  if (type === "feedback") {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("Feedback");
    if (!sheet) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "error", message: "Feedback tab not found"
      })).setMimeType(ContentService.MimeType.JSON);
    }
    sheet.appendRow([
      p.project || "",
      p.feedback_type || "",
      "'" + (p.timestamp || ""),
      p.content || "",
      p.priority || "",
      new Date(),
      p.pin || "",
      ""
    ]);

    try {
      var feedbackType = p.feedback_type || "feedback";
      var subject = "[Rsquare] " + (p.project || "Unknown") + " - New " + feedbackType;
      var body = "Project: " + (p.project || "Unknown") + "\n" +
                 "Type: " + feedbackType + "\n";
      if (p.timestamp) body += "Timestamp: " + p.timestamp + "\n";
      body += "Content: " + (p.content || "") + "\n";
      if (p.priority) body += "Priority: " + p.priority + "\n";
      body += "\nSubmitted: " + new Date().toLocaleString() + "\n";
      body += "\nView all feedback: https://portfolio.rsquarestudios.com/feedback/?role=editor";
      MailApp.sendEmail({ to: FEEDBACK_EMAIL_EDITOR, cc: FEEDBACK_EMAIL_RAM, subject: subject, body: body });
    } catch(err) { Logger.log("Email failed: " + err); }

    return ContentService.createTextOutput(JSON.stringify({
      status: "ok", message: "Feedback saved"
    })).setMimeType(ContentService.MimeType.JSON);
  }

  // ── Helper: verify PIN by checking it matches a known PIN in the Feedback tab ──
  // For feedback_update and feedback_notify, the caller must provide a PIN
  // that matches at least one existing row for that project.
  function verifyProjectPin(sheet, project, pin) {
    if (!pin) return false;
    var rows = sheet.getDataRange().getValues();
    for (var i = 1; i < rows.length; i++) {
      // Column A = Project, Column G (index 6) = PIN
      if (rows[i][0] == project && rows[i][6] == pin) return true;
    }
    return false;
  }

  // Update fixed status (no email — editor uses Notify button for summary)
  if (type === "feedback_update") {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("Feedback");
    if (!sheet) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "error", message: "Feedback tab not found"
      })).setMimeType(ContentService.MimeType.JSON);
    }
    // Verify caller has a valid PIN for this project
    if (!p.pin || !verifyProjectPin(sheet, p.project, p.pin)) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "error", message: "Unauthorized"
      })).setMimeType(ContentService.MimeType.JSON);
    }
    var rows = sheet.getDataRange().getValues();
    var found = false;
    for (var i = 1; i < rows.length; i++) {
      if (rows[i][0] == p.project && rows[i][2] == p.timestamp && rows[i][3] == p.content) {
        // Column H: "yes", "cant_fix:reason", or ""
        var val = "";
        if (p.fixed === "yes") val = "yes";
        else if (p.fixed === "cant_fix") val = "cant_fix:" + (p.note || "");
        sheet.getRange(i + 1, 8).setValue(val);
        found = true;
        break;
      }
    }
    return ContentService.createTextOutput(JSON.stringify({
      status: found ? "ok" : "not_found",
      message: found ? "Status updated" : "Correction row not found"
    })).setMimeType(ContentService.MimeType.JSON);
  }

  // Summary notification from editor (one email for all fixes)
  if (type === "feedback_notify") {
    // Verify caller has a valid PIN for this project
    var ss2 = SpreadsheetApp.getActiveSpreadsheet();
    var sheet2 = ss2.getSheetByName("Feedback");
    if (sheet2 && !verifyProjectPin(sheet2, p.project, p.pin)) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "error", message: "Unauthorized"
      })).setMimeType(ContentService.MimeType.JSON);
    }

    try {
      var subject = "[Rsquare] " + (p.project || "Unknown") + " - Editor update";
      var body = p.summary || "No details provided.";
      body += "\n\nView all: https://portfolio.rsquarestudios.com/feedback/?role=editor";
      MailApp.sendEmail({ to: FEEDBACK_EMAIL_RAM, subject: subject, body: body });
    } catch(err) { Logger.log("Email failed: " + err); }

    return ContentService.createTextOutput(JSON.stringify({
      status: "ok", message: "Notification sent"
    })).setMimeType(ContentService.MimeType.JSON);
  }

  // ── Booking request from quote builder ──
  if (type === "booking") {
    var ss3 = SpreadsheetApp.getActiveSpreadsheet();
    var bookingSheet = ss3.getSheetByName("Bookings");
    if (!bookingSheet) {
      bookingSheet = ss3.insertSheet("Bookings");
      bookingSheet.appendRow(["Name", "Event", "Date", "Hours", "Coverage", "Quote", "Live Streaming", "Location", "Submitted", "Status"]);
    }
    bookingSheet.appendRow([
      p.name || "",
      p.event || "",
      p.date || "",
      p.hours || "",
      p.coverage || "",
      p.quote || "",
      p.live_streaming || "No",
      p.location || "",
      new Date(),
      "new"
    ]);

    try {
      var subject = "[Rsquare] New Booking Request — " + (p.name || "Unknown");
      var body = "New booking request from the website!\n\n" +
                 "Client: " + (p.name || "") + "\n" +
                 "Event: " + (p.event || "") + "\n" +
                 "Date: " + (p.date || "TBD") + "\n" +
                 "Location: " + (p.location || "") + "\n" +
                 "Hours: " + (p.hours || "") + "\n" +
                 "Coverage: " + (p.coverage || "") + "\n" +
                 "Live Streaming: " + (p.live_streaming || "No") + "\n" +
                 "Quote: " + (p.quote || "") + "\n\n" +
                 "Submitted: " + new Date().toLocaleString() + "\n";
      MailApp.sendEmail({ to: FEEDBACK_EMAIL_RAM, subject: subject, body: body });
    } catch(err) { Logger.log("Booking email failed: " + err); }

    return ContentService.createTextOutput(JSON.stringify({
      status: "ok", message: "Booking request saved"
    })).setMimeType(ContentService.MimeType.JSON);
  }

  // ── Default: Review submission ──
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Reviews");
  sheet.appendRow([
    p.name || "",
    p.event_type || "",
    p.rating || 5,
    p.review || "",
    new Date().toISOString().split("T")[0],
    "pending"
  ]);

  return ContentService.createTextOutput(JSON.stringify({
    status: "ok"
  })).setMimeType(ContentService.MimeType.JSON);
}
