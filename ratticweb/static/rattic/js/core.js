function credsearch() {
    var searchstr = document.forms["search"]["box"].value
    window.location = "/cred/list-by-search/" + searchstr + "/";
    return false;
}

