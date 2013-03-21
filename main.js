$.ajax({
    url: "/games",
    type: "GET"
}).done(function(data) {
    build_gamelist(data);
});
