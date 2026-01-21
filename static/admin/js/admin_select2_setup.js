// Wait for the document to be ready
$(document).ready(function () {
  // Check if Select2 is loaded
  if ($.fn.select2) {
    $(".advanced-select").select2({
      width: "100%",
      allowClear: true,
      closeOnSelect: false,
      placeholder: function () {
        $(this).data("placeholder");
      },
      // This enables the tags to look like the "Pills" in your design
      templateSelection: function (data, container) {
        return data.text;
      },
    });
  } else {
    console.error("Select2 failed to load!");
  }
});
