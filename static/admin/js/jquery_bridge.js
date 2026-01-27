/* admin/js/jquery_bridge.js */
(function () {
  // 1. Check if Django's jQuery is loaded
  var djangoJQuery =
    window.django && window.django.jQuery ? window.django.jQuery : null;

  // 2. If global jQuery is missing, use Django's
  if (!window.jQuery && djangoJQuery) {
    window.jQuery = djangoJQuery;
    window.$ = djangoJQuery;
    console.log("✅ jQuery Bridge: Aliased django.jQuery to window.jQuery");
  } else if (window.jQuery) {
    console.log("✅ jQuery Bridge: Global jQuery already exists.");
  } else {
    console.warn("⚠️ jQuery Bridge: No jQuery found!");
  }
})();
