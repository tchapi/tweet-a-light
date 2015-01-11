<!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Totem #{{ instance_id }}</title>
    <style type="text/css">

      @import url(http://fonts.googleapis.com/css?family=Oswald);

      html, body {
        background: #00BCD4;
        color: white;
        text-align: center;
        padding-top: 20px;
        padding-bottom: 20px;
        margin: 0;
        font-family: "Oswald", "Helvetica Neue", "Helvetica", "Verdana", "Arial", sans-serif;
      }

      a {
        color: #007890;
        text-decoration: none;
      }

      a:hover {
        color: #00DEF6;
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
        color: #00ABC3;
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
        color: #00DEF6;
      }
      div.status div.legend img{
        margin-right: 5px;
        opacity: 0.35;
      }
      div.status em {
        color: #009AB2;
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
        color: #009AB2;
        text-transform: uppercase;
        background: #00CDE5;
        width: 300px;
        padding: 10px;
        margin: 5px;
      }
      *::-webkit-input-placeholder {
          color: #00ABC3;
      }
      *:-moz-placeholder {
          /* FF 4-18 */
          color: #00ABC3;
      }
      *::-moz-placeholder {
          /* FF 19+ */
          color: #00ABC3;
      }
      *:-ms-input-placeholder {
          /* IE 10+ */
          color: #00ABC3;
      }

      label {
        width: 160px;
        display: inline-block;
        text-align: right;
      }

      .fb_page {
        position: absolute;
        padding: 8px 0;
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
      <div><label for="hashtag">Hashtag :</label><input id="hashtag" name="hashtag" value="{{ hashtag }}" type="text" class="hashtag" placeholder="#hashtag" onfocus="this.select();" onmouseup="return false;"></div>
      <div><label for="complementary">Power hashtag :</label><input id="complementary" name="complementary" value="{{ hashtag_complementary }}" type="text" class="hashtag power" placeholder="#powertag" onfocus="this.select();" onmouseup="return false;"></div>
      <div><label for="facebook">Facebook page :</label><input id="facebook" name="facebook" value="{{ fb_page }}" type="text" placeholder="pagename" onfocus="this.select();" onmouseup="return false;"><a href="http://graph.facebook.com/{{ fb_page }}/" target="_blank" class="fb_page" title="Go to page">▶</a></div>
    </div>

  </body>
</html>
