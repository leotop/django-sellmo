module.exports = 
  paths:
    src: './src/'
    build: './build/'
    dist: './dist/'
  browserify:
    bundles: [
      {entries: ['coffee/plugins/index.coffee'], output: 'plugins.js'}
    ]
  less: 
    sources: ['less/screen.less']
  stylesheets: 
    entries: [
      'screen.css' 
    ]
    output: 'shop/css/shop.css'
  javascripts:
    entries: [
      'bower_components/jquery/dist/jquery.js',
      'plugins.js',
    ]
    output: 'shop/js/shop.js'