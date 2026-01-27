// // Wait for the document to be ready
// $(document).ready(function () {
//   // Check if Select2 is loaded
//   if ($.fn.select2) {
//     $(".advanced-select").select2({
//       width: "100%",
//       allowClear: true,
//       closeOnSelect: false,
//       placeholder: function () {
//         $(this).data("placeholder");
//       },
//       // This enables the tags to look like the "Pills" in your design
//       templateSelection: function (data, container) {
//         return data.text;
//       },
//     });
//   } else {
//     console.error("Select2 failed to load!");
//   }
// });

/* static/admin/js/admin_select2_setup.js */
(function ($) {
  $(document).ready(function () {
    function initSelect2(element) {
      $(element).select2({
        width: "100%",
        allowClear: true,
        placeholder: $(element).data("placeholder") || "Select or Type...",

        // CRITICAL: This allows typing new values
        tags: true,

        // Optional: Helper to handle the "New Tag" creation visually
        createTag: function (params) {
          var term = $.trim(params.term);
          if (term === "") {
            return null;
          }
          return {
            id: term,
            text: term,
            newTag: true, // add a marker
          };
        },
      });
    }

    // 1. Initialize on existing fields
    initSelect2(".advanced-select");

    // 2. Initialize on new rows added via "Add another" (Inline forms)
    // This is required if you are using TabularInline or StackedInline
    $(document).on("formset:added", function (event, $row, formsetName) {
      $row.find(".advanced-select").each(function () {
        initSelect2(this);
      });
    });
  });
})(jQuery || django.jQuery);
