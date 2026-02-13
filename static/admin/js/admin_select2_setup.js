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

window.addEventListener("load", function () {
  // 1. Get Jazzmin's jQuery
  var $ = window.django ? window.django.jQuery : window.jQuery;
  if (!$) {
    console.error("jQuery not found");
    return;
  }

  // 2. Load Select2 Dynamically (Fixes the "missing $" crash)
  var script = document.createElement("script");
  script.src =
    "https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.full.min.js";
  script.onload = function () {
    // This runs only after Select2 is fully loaded
    initMyAdmin($);
  };
  document.head.appendChild(script);

  function initMyAdmin($) {
    // --- PART A: FIX THE TABS ---
    if (window.location.hash) {
      var hash = window.location.hash;
      var $tabLink = $('a[href="' + hash + '"]');
      if ($tabLink.length > 0) {
        // Use standard click if bootstrap tab() isn't exposed
        $tabLink[0].click();
      }
    }

    // --- PART B: SETUP DROPDOWNS ---
    function applySelect2(element) {
      $(element).select2({
        width: "100%",
        allowClear: true,
        placeholder: $(element).data("placeholder") || "Select or Type...",
        tags: true,
        createTag: function (params) {
          var term = $.trim(params.term);
          if (term === "") return null;
          return { id: term, text: term, newTag: true };
        },
      });
    }

    $(".advanced-select").each(function () {
      applySelect2(this);
    });

    // Handle Inline Rows
    $(document).on("formset:added", function (event, $row) {
      $row.find(".advanced-select").each(function () {
        applySelect2(this);
      });
    });
  }
});
