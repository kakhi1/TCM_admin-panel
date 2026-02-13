// /* static/admin/js/admin_select2_setup.js */
// (function ($) {
//   $(document).ready(function () {
//     function initSelect2(element) {
//       $(element).select2({
//         width: "100%",
//         allowClear: true,
//         placeholder: $(element).data("placeholder") || "Select or Type...",

//         // CRITICAL: This allows typing new values
//         tags: true,

//         // Optional: Helper to handle the "New Tag" creation visually
//         createTag: function (params) {
//           var term = $.trim(params.term);
//           if (term === "") {
//             return null;
//           }
//           return {
//             id: term,
//             text: term,
//             newTag: true, // add a marker
//           };
//         },
//       });
//     }

//     // 1. Initialize on existing fields
//     initSelect2(".advanced-select");

//     // 2. Initialize on new rows added via "Add another" (Inline forms)
//     // This is required if you are using TabularInline or StackedInline
//     $(document).on("formset:added", function (event, $row, formsetName) {
//       $row.find(".advanced-select").each(function () {
//         initSelect2(this);
//       });
//     });
//   });
// })(jQuery || django.jQuery);
/* file: static/admin/js/admin_select2_setup.js */

// We use 'window.addEventListener' to ensure Jazzmin's jQuery is fully loaded
window.addEventListener("load", function () {
  // 1. SAFE JQUERY RESOLUTION
  // Jazzmin usually puts jQuery in 'django.jQuery' or 'window.jQuery'
  var $ = window.django ? window.django.jQuery : window.jQuery;

  if (!$) {
    console.error("jQuery not found. Select2 and Tabs cannot initialize.");
    return;
  }

  // --- PART A: FIX THE TABS (The URL Hash Logic) ---
  if (window.location.hash) {
    var hash = window.location.hash; // e.g. "#medicine-tcm-diagnoses-tab"

    // Jazzmin/Bootstrap tabs are links <a>. We try to find the one matching the hash.
    var $tabLink = $('a[href="' + hash + '"]');

    // If found, click it to switch the tab
    if ($tabLink.length > 0) {
      $tabLink.tab("show"); // Bootstrap standard
      // Or fallback if .tab() isn't available:
      // $tabLink.click();
    }
  }

  // --- PART B: INITIALIZE SELECT2 ---
  function initSelect2(element) {
    $(element).select2({
      width: "100%",
      allowClear: true,
      placeholder: $(element).data("placeholder") || "Select or Type...",
      tags: true, // CRITICAL: Allows typing new values
      createTag: function (params) {
        var term = $.trim(params.term);
        if (term === "") {
          return null;
        }
        return {
          id: term,
          text: term,
          newTag: true,
        };
      },
    });
  }

  // Initialize on existing fields
  $(".advanced-select").each(function () {
    initSelect2(this);
  });

  // Initialize on new rows (for Inlines)
  $(document).on("formset:added", function (event, $row, formsetName) {
    $row.find(".advanced-select").each(function () {
      initSelect2(this);
    });
  });
});
