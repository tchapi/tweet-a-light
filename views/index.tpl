<!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Totem #{{ instance_id }}</title>
    <style type="text/css">

      @import url(http://fonts.googleapis.com/css?family=Oswald);
      <%
        base_color = "#" + '{0:06X}'.format(color)
        dark_color = "#" + '{0:06X}'.format(color - 0x001111)
        darker_color = "#" + '{0:06X}'.format(color - 0x002222)
        light_color = "#" + '{0:06X}'.format(color + 0x001111)
        lighter_color = "#" + '{0:06X}'.format(color + 0x002222)

        link_color = "#" + '{0:06X}'.format(color - 0x004444)
      %>
      html, body {
        color: white;
        text-align: center;
        padding-top: 20px;
        padding-bottom: 20px;
        margin: 0;
        font-family: "Oswald", "Helvetica Neue", "Helvetica", "Verdana", "Arial", sans-serif;
        background: {{ base_color }};
      }

      a {
        text-decoration: none;
        color: {{ link_color }};
      }

      a:hover {
        color: {{ lighter_color }};
      }

      div.title > h1 {
        text-transform: uppercase;
        font-size: 6em;
        line-height: 1em;
        margin-bottom: 10px;
        margin-top: 20px;
      }
      div.title > h1 > span{
        text-transform: uppercase;
        color: {{ dark_color }};
      }


      div.title > h2 {
        text-transform: uppercase;
        font-size: 1.2em;
        margin: 5px;
      }

      div.status {
        text-transform: uppercase;
        margin-top: 50px;
      }
      div.status div.figure {
        font-size: 5em;
        line-height: 1em;
        box-shadow: 0 10px 5px -5px rgba(#000, 0.2);
      }
      div.status div.legend {
        font-size: 2em;
        color: {{ lighter_color }};
      }
      div.status div.legend img{
        margin-right: 5px;
        opacity: 0.35;
      }
      div.status em {
        color: {{ darker_color }};
      }
      div.config {
        text-transform: uppercase;
        margin-top: 100px;
      }
      div.config > div.title {
        color : lightgray;
      }

      img {
        margin: 0;
      }

      input {
        border: none;
        outline: none;
        color: {{ darker_color }};
        text-transform: uppercase;
        width: 300px;
        padding: 10px;
        margin: 5px;
        background: {{ light_color }};
      }
      *::-webkit-input-placeholder {
          color: {{ dark_color }};
      }
      *:-moz-placeholder {
          /* FF 4-18 */
          color: {{ dark_color }};
      }
      *::-moz-placeholder {
          /* FF 19+ */
          color: {{ dark_color }};
      }
      *:-ms-input-placeholder {
          /* IE 10+ */
          color: {{ dark_color }};
      }

      label {
        width: 160px;
        display: inline-block;
        text-align: right;
      }

      .button_right {
        position: absolute;
        padding: 8px 0;
        cursor: pointer;
      }

      .button_page {
        position: absolute;
        margin-left: -22px;
        padding: 8px 0;
        cursor: pointer;
      }

    </style>
  </head>
  <body>

    <div class="title">
      <img src="/static/logo.png" alt="Logo" width="400px" height="200px">
      <h1>TOTEM <span>#{{ instance_id }}</span></h1>
      <h2>by <a href="http://ckab.com">CKAB</a> + <a href="http://facebook.com/draftateliers">Draft Ateliers</a> + <a href="http://www.aogitsune.com/">AO Gitsune</a></h2>
    </div>

    <div class="status">
      <div class="figure">{{ fb_likes }}</div>
      <div class="legend"><img src="/static/fb.png" width="30px" height="30px"> Facebook likes</div>
      <em>up {{ percentage }}% since startup</em>
    </div>

    <div class="config">
      <div class="title">Configuration</div>
      <div><label for="hashtag">Hashtag :</label><input id="hashtag" name="hashtag" value="{{ hashtag }}" type="text" class="hashtag" placeholder="#hashtag"><a class="button_right" id="save_hashtag" onClick="change_hashtag()">Save</a></div>
      <div><label for="complementary">Power hashtag :</label><input id="complementary" name="complementary" value="{{ hashtag_complementary }}" type="text" class="hashtag power" placeholder="#powertag"><a class="button_right" id="save_complementary" onClick="change_complementary_hashtag()">Save</a></div>
      <div><label for="facebook">Facebook page :</label><input id="facebook" name="facebook" value="{{ fb_page }}" type="text" placeholder="pagename"><a href="http://graph.facebook.com/{{ fb_page }}/" target="_blank" class="button_page" title="Go to page">▶</a><a class="button_right" id="save_facebook" onClick="change_page()">Save</a></div>
    </div>

    <script type="text/javascript">

    var change_hashtag = function() {
      var url = "/hashtag";
      var params = "hashtag=" + document.getElementById('hashtag').value;
      send_post(url, params);
    };

    var change_complementary_hashtag = function() {
      var url = "/hashtag/complementary";
      var params = "complementary_hashtag=" + document.getElementById('complementary').value;
      send_post(url, params);
    };

    var change_page = function() {
      var url = "/facebook";
      var params = "page=" + document.getElementById('facebook').value;
      send_post(url, params);
      // Now reload page
      window.location.reload()
    };

    var send_post = function(url, params) {
      var http = new XMLHttpRequest();

      http.open("POST", url, true);

      //Send the proper header information along with the request
      http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
      http.setRequestHeader("Content-length", params.length);
      http.setRequestHeader("Connection", "close");

      http.onreadystatechange = function() {//Call a function when the state changes.
        if(http.readyState == 4 && http.status == 200) {
          console.log(http.responseText);
        }
      }
      http.send(params);
    }



    </script>
  </body>
</html>
