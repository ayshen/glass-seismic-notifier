/* Geocoder for dashboard. Converts user-supplied place names into coordinates
for use by the seismic notifier.
Requires Google Maps library.
    https://maps.googleapis.com/maps/api/js?sensor=false
*/
function onGeocodeResult(results, geocoderStatus) {
    var geocodeOutput = document.getElementById("geocode-output");
    var pleaseContact = "";
    switch(geocoderStatus) {
    case google.maps.GeocoderStatus.ERROR:
        geocodeOutput.classList.add("geocode-error");
        geocodeOutput.innerHTML = "Can&#39;t reach Google Maps. Check your internet connection.";
        break;
    case google.maps.GeocoderStatus.INVALID_REQUEST:
        geocodeOutput.classList.add("geocode-error");
        geocodeOutput.innerHTML = "Can&#39;t convert to a location." +
                pleaseContact;
        break;
    case google.maps.GeocoderStatus.OVER_QUERY_LIMIT:
        geocodeOutput.classList.add("geocode-error");
        geocodeOutput.innerHTML = "I&#39;ve made too many geocoding requests." +
                pleaseContact;
        break;
    case google.maps.GeocoderStatus.REQUEST_DENIED:
        geocodeOutput.classList.add("geocode-error");
        geocodeOutput.innerHTML = "I&#39;m not allowed to ask Google Maps to " +
                "convert places into coordinates." + pleaseContact;
        break;
    case google.maps.GeocoderStatus.UNKNOWN_ERROR:
        geocodeOutput.classList.add("geocode-error");
        geocodeOutput.innerHTML = "Something went wrong. Please try again.";
        break;
    case google.maps.GeocoderStatus.ZERO_RESULTS:
        geocodeOutput.classList.add("geocode-error");
        geocodeOutput.innerHTML = "That doesn&#39;t look like " +
                "an actual place&hellip;";
        break;
    case google.maps.GeocoderStatus.OK:
        var latLng = results[0].geometry.location;
        document.getElementById("lng").value = latLng.lng();
        document.getElementById("lat").value = latLng.lat();
        geocodeOutput.classList.remove("geocode-error");
        geocodeOutput.innerHTML = "(" + latLng.lng() + ", " + latLng.lat() + ")";
        break;
    default:
        console.error("strange GeocoderStatus", geocoderStatus);
        geocodeOutput.innerHTML = "";
        break;
    }
}
function geocodeLoi() {
    if(window.loiChanged) {
        window.loiChanged = false;
        if("" + document.getElementById("loi").value === "") return;
        window.geocoder.geocode(
                {"address": document.getElementById("loi").value},
                onGeocodeResult);
    }
}
function onLoiChanged() {
    window.loiChanged = true;
}
function init() {
    window.loiChanged = false;
    window.geocoder = new google.maps.Geocoder();
    window.loiChangeListener = google.maps.event.addDomListener(
            document.getElementById("loi"),
            "keyup",
            onLoiChanged);
    window.interval_geocodeLoi = setInterval(geocodeLoi, 1000);
}
function dispose() {
    clearInterval(window.interval_geocodeLoi);
    google.maps.event.removeListener(window.loiChangeListener);
    google.maps.event.removeListener(window.windowLoadListener);
    google.maps.event.removeListener(window.windowUnloadListener);
    window.loiChanged = undefined;
    window.geocoder = undefined;
    window.windowLoadListener = undefined;
    window.windowUnloadListener = undefined;
    window.loiChangeListener = undefined;
    window.interval_geocodeLoi = undefined;
}
window.windowLoadListener = google.maps.event.addDomListener(window, "load", init);
window.windowUnloadListener = google.maps.event.addDomListener(window, "unload", dispose);
