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

/* file: static/admin/js/admin_select2_setup.js */

// CRITICAL: Map standard jQuery to django.jQuery to fix "change_form.js" errors
if (!window.django) window.django = {};
if (!window.django.jQuery) window.django.jQuery = window.jQuery;

(function ($) {
  $(document).ready(function () {
    // --- PART A: FIX THE TABS ---
    if (window.location.hash) {
      var hash = window.location.hash;
      var $tabLink = $('a[href="' + hash + '"]');

      if ($tabLink.length > 0) {
        // Try Bootstrap tab show
        try {
          $tabLink.tab("show");
        } catch (e) {
          // Fallback to click if Bootstrap isn't fully ready
          $tabLink.click();
        }
      } else {
        // Fallback for specific Jazzmin structure
        $('.nav-tabs a[href="' + hash + '"]').tab("show");
      }
    }

    // --- PART B: SETUP SELECT2 ---
    function initSelect2(element) {
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

    // Initialize on existing fields
    $(".advanced-select").each(function () {
      initSelect2(this);
    });

    // Initialize on new rows (Inline Forms)
    $(document).on("formset:added", function (event, $row) {
      $row.find(".advanced-select").each(function () {
        initSelect2(this);
      });
    });
  });
})(window.jQuery);
