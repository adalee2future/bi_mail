from IPython.display import HTML
HTML('''
<script>
  code_show=true;
  function code_toggle()
  {
    if (code_show)
      { $('div.input').hide(); }
    else
      { $('div.input').show(); }

    code_show = !code_show
  }
  $( document ).ready(code_toggle);
</script>

<form action="javascript:code_toggle()">
  <input type="submit" value="点击此处隐藏或者显示代码">
</form>
''')

