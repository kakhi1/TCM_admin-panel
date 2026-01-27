// /* static/admin/js/unsaved_changes.js */

// window.addEventListener("load", function () {
//   // 1. Safely locate jQuery (Django's version or Standard version)
//   var $ =
//     typeof django !== "undefined" && django.jQuery
//       ? django.jQuery
//       : window.jQuery || null;

//   if (!$) {
//     console.warn(
//       "Unsaved Changes Script: jQuery not found. Validation skipped.",
//     );
//     return;
//   }

//   $(document).ready(function () {
//     var formModified = false;

//     // 2. Detect changes on inputs (excluding search bar)
//     $(
//       "form#analysis_form :input, form#pattern_form :input, .change-form form :input",
//     )
//       .not("#searchbar")
//       .on("change keyup", function () {
//         formModified = true;
//       });

//     // 3. Specific handler for Custom Widgets
//     $(".advanced-select, .sync-input, .sync-select").on("change", function () {
//       formModified = true;
//     });

//     // 4. Warn on Page Exit
//     window.onbeforeunload = function () {
//       if (formModified) {
//         return "You have unsaved changes. Are you sure you want to leave without saving?";
//       }
//     };

//     // 5. Allow legitimate submissions (Save buttons)
//     $("form").on("submit", function () {
//       formModified = false;
//     });

//     // 6. Session Keep-Alive (Ping every 5 mins)
//     setInterval(function () {
//       var pingUrl = window.location.href;
//       $.get(pingUrl);
//       console.log("Session Keep-Alive Ping sent.");
//     }, 300000);
//   });
// });

/* static/admin/js/unsaved_changes.js */

window.addEventListener("load", function () {
  var $ =
    typeof django !== "undefined" && django.jQuery
      ? django.jQuery
      : window.jQuery || null;

  if (!$) return;

  $(document).ready(function () {
    var formModified = false;

    // 1. Target ANY input inside the main change form
    // Django Admin uses #content-main form or .change-form
    $(document).on(
      "change keyup",
      "#content-main form :input, .change-form form :input",
      function () {
        if ($(this).attr("id") !== "searchbar") {
          formModified = true;
        }
      },
    );

    // 2. Explicitly watch the custom widgets for WBC Matrix and Score Defs
    // Added .vTextField and textarea to ensure ScoreDefAdminForm is covered
    $(document).on(
      "change",
      ".advanced-select, .sync-input, .sync-select, .paired-widget-wrapper :input",
      function () {
        formModified = true;
      },
    );

    // 3. Prevent the warning when clicking "Save" or "Save and continue"
    $(document).on("submit", "form", function () {
      formModified = false;
    });

    window.onbeforeunload = function () {
      if (formModified) {
        return "You have unsaved changes. Are you sure you want to leave?";
      }
    };

    // Keep-alive ping
    setInterval(function () {
      $.get(window.location.href);
    }, 300000);
  });
});
