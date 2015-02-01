var gulp = require('gulp');
var less = require('gulp-less');
var coffee = require('gulp-coffee');
var sourcemaps = require('gulp-sourcemaps');
var util = require('gulp-util');


var paths = {
  less: {
    entries:  ['./src/less/screen.less', './src/less/print.less'],
    watch: ['./src/less/**/*.less']
  },
  coffee: {
    entries:  ['./src/coffee/**/*.coffee'],
    watch: ['./src/coffee/**/*.coffee']
  }
}


var onError = function(err) {
  util.log(util.colors.red(err));
  util.beep();
  this.emit('end');
}


gulp.task('less', function() {
  var src = gulp.src(paths.less.entries)
    .pipe(sourcemaps.init())
    .pipe(less())
    .pipe(sourcemaps.write())
    .on('error', onError)
    .pipe(gulp.dest('./build/css'))
});


gulp.task('coffee', function() {
  var src = gulp.src(paths.coffee.entries)
    .pipe(sourcemaps.init())
    .pipe(coffee())
    .pipe(sourcemaps.write())
    .on('error', onError)
    .pipe(gulp.dest('./build/js'))
});


gulp.task('watch', ['less', 'coffee'], function() {
  gulp.watch(paths.less.watch, ['less']);
  gulp.watch(paths.coffee.watch, ['coffee']);
});


gulp.task('default', ['watch']);
