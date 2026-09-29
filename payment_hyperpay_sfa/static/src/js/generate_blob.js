// Reference
// https://dev.to/pulljosh/how-to-load-html-css-and-js-code-into-an-iframe-2blc

export function getGeneratedPageURL({ html, css, js }) {
    const getBlobURL = (code, type) => {
        const blob = new Blob([code], { type });
        return URL.createObjectURL(blob);
    };

    const source = `
        <html>
          <head>
            ${css}
            ${js}
          </head>
          <body>
          <script>
          var wpwlOptions = {
                onReady: function(){
                  var shopOrigin = $('input[name="shopOrigin"]');
                  var origin = parent.window.location.origin;
                  parent_iframe = $('#hyperpay_iframe', window.parent.document);
                  parent_iframe.css({"width":"100%", "height":"21em", "border":"none", "display":""});
                  $('.hyperpay_loader', window.parent.document).remove();
                  $('#hyperpay_close', window.parent.document).on('click', function(){
                      parent.window.location.reload(true);
                      });
                  if (shopOrigin.length != 0 && shopOrigin.val() == 'null'){
                      shopOrigin.val(origin);
                  }
                }
              }
              $(document).ready(function(){
                setTimeout(function(){
                  var parent_frame = window.parent.$("#hyperpay_iframe")
                  if(parent_frame.css('display') == 'none'){
                    $('.hyperpay_loader', window.parent.document).remove();
                    parent_frame.css({"display":"block","width":"100%", "height":"21em", "border":"none"});
                    $('#hyperpay_close', window.parent.document).on('click', function(){
                      parent.window.location.reload();
                    });
                  }
                }, 3000);
              });
              </script>
            ${html || ''}
          </body>
        </html>
      `;

    return getBlobURL(source, 'text/html');
}