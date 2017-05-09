var gulp = require('gulp');
var sass = require('gulp-sass');
var browserSync = require('browser-sync').create();
var header = require('gulp-header');
var cleanCSS = require('gulp-clean-css');
var concat = require('gulp-concat');
var clean = require('gulp-rimraf');
var rename = require('gulp-rename');
var uglify = require('gulp-uglify');
var autoprefixer = require('gulp-autoprefixer');
var pkg = require('./package.json');
var imagemin = require('gulp-imagemin');
var cache = require('gulp-cache');
var runSequence = require('run-sequence');
var sourcemaps = require('gulp-sourcemaps');
var handlebars = require('gulp-compile-handlebars');
var fs = require('fs');
var yaml = require('yaml-js');
var exec = require('child_process').exec;
var gutil = require('gulp-util');
var argv  = require('minimist')(process.argv);
var rsync = require('gulp-rsync');
var prompt = require('gulp-prompt');
var gulpif = require('gulp-if');

// Set the banner content
var banner = ['/*\n',
    ' * <%= pkg.title %> v<%= pkg.version %> (<%= pkg.homepage %>)\n',
    ' * Copyright 2016-' + (new Date()).getFullYear(), ' <%= pkg.author %>\n',
    ' * Licensed under <%= pkg.license.type %>\n',
    ' */\n',
    ''
].join('');

// Clean
gulp.task('clean', function() {
  console.log("Clean all files in build folder");
  return gulp.src("build/*", { read: false })
    .pipe(clean());
});

// Minify compiled CSS
gulp.task('minify-css:inner', function() {
    return gulp.src('src/sass/**/*.scss')
        .pipe(sass().on('error', sass.logError))
        .pipe(autoprefixer('last 2 versions'))
        .pipe(header(banner, { pkg: pkg }))
        .pipe(gulp.dest('build/css'))
        .pipe(sourcemaps.init())
            .pipe(cleanCSS({ compatibility: 'ie8' }))
        .pipe(sourcemaps.write())
        .pipe(rename({ suffix: '.min' }))
        .pipe(gulp.dest('build/css'))
        .pipe(browserSync.reload({
            stream: true
        }))
});

gulp.task('minify-css:clean', function() {
    return gulp.src('build/css/**/*.css', { read: false })
        .pipe(clean());
});
gulp.task('minify-css', function(cb) {
    runSequence('minify-css:clean', 'minify-css:inner', cb);
});

// Minify JS
gulp.task('minify-js:inner', function() {
    return gulp.src('src/js/**/*.js')
        // .pipe(concat('main.js'))
        .pipe(gulp.dest('build/js'))
        // .pipe(sourcemaps.init())
            // .pipe(uglify())
        // .pipe(sourcemaps.write())
        // .pipe(header(banner, { pkg: pkg }))
        // .pipe(rename({ suffix: '.min' }))
        // .pipe(gulp.dest('build/js'))
        .pipe(browserSync.reload({
            stream: true
        }))
});
gulp.task('minify-js:clean', function() {
    return gulp.src('build/js/**/*.js', { read: false })
        .pipe(clean());
});
gulp.task('minify-js', function(cb) {
    runSequence('minify-js:clean', 'minify-js:inner', cb);
});

// Copy vendor libraries from /node_modules into /build/vendor
gulp.task('copy', function() {
    gulp.src(['node_modules/bootstrap/dist/**/*', '!**/npm.js', '!**/bootstrap-theme.*'])
        .pipe(gulp.dest('build/vendor/bootstrap'))

    gulp.src(['node_modules/jquery/dist/**/*'])
        .pipe(gulp.dest('build/vendor/jquery'))

    gulp.src([
            'node_modules/font-awesome/**',
            '!node_modules/font-awesome/.npmignore',
            '!node_modules/font-awesome/*.txt',
            '!node_modules/font-awesome/*.md',
            '!node_modules/font-awesome/*.json'
        ])
        .pipe(gulp.dest('build/vendor/font-awesome'))
});

// Copy .html files from /src to /build
gulp.task('html:inner', function() {
    return gulp.src(['src/**/*.html'])
        .pipe(gulp.dest('build'))
        .pipe(browserSync.reload({
            stream: true
        }));
});
gulp.task('html:clean', function() {
    return gulp.src('build/**/*.html', { read: false })
        .pipe(clean());
});
gulp.task('html', function(cb) {
    runSequence('html:clean', 'html:inner', cb);
});

// Copy and optimise images
gulp.task('images:inner', function(){
    return gulp.src('src/img/**/*')
        .pipe(cache(imagemin({ optimizationLevel: 3, progressive: true, interlaced: true })))
        .pipe(gulp.dest('build/img/'))
        .pipe(browserSync.reload({
            stream: true
        }));
});
gulp.task('images:clean', function() {
    return gulp.src('build/img/**/*', { read: false })
        .pipe(clean());
});
gulp.task('images', function(cb) {
    runSequence('images:clean', 'images:inner', cb);
});

// Copy documents
gulp.task('data:inner', function(){
    return gulp.src('src/data/**/*')
        .pipe(gulp.dest('build/data/'));
});
gulp.task('data:clean', function() {
    return gulp.src('build/data/**/*', { read: false })
        .pipe(clean());
});
gulp.task('data', function(cb) {
    runSequence('data:clean', 'data:inner', cb);
});

// Copy fonts
gulp.task('fonts:inner', function(){
    return gulp.src('src/fonts/**/*')
        .pipe(gulp.dest('build/fonts/'));
});
gulp.task('fonts:clean', function() {
    return gulp.src('build/fonts/**/*', { read: false })
        .pipe(clean());
});
gulp.task('fonts', function(cb) {
    runSequence('fonts:clean', 'fonts:inner', cb);
});

// Configure the browserSync task
gulp.task('browserSync', function() {
    browserSync.init({
        server: {
            baseDir: 'build/'
        },
    })
});

// Deploy
gulp.task('deploy', function() {

  rsyncPaths = ['build/**/*'];

  rsyncConf = {
    progress: true,
    incremental: true,
    relative: true,
    emptyDirectories: true,
    recursive: true,
    clean: true,
    exclude: [],
    root: 'build'
  };

  if (argv.dev) {
    rsyncConf.hostname = 'davidbarrell.me';
    // rsyncConf.username = '';
    rsyncConf.destination = '/home/ubuntu/davidbarrell.me/html/ccc/';
  //  } else if (argv.prod) {
  //   rsyncConf.hostname = '';
  //   rsyncConf.username = '';
  //   rsyncConf.destination = '';
  } else {
    throwError('deploy', gutil.colors.red('Missing or invalid target'));
  }

  // runSequence('default');

  return gulp.src(rsyncPaths)
  .pipe(gulpif(
      argv.prod,
      prompt.confirm({
        message: 'Heads Up! Are you SURE you want to push to PRODUCTION?',
        default: false
      })
  ))
  .pipe(rsync(rsyncConf));
});

// Run everything
gulp.task('default', ['minify-css', 'minify-js', 'copy', 'html', 'images', 'data', 'fonts']);

// Dev task with browserSync
gulp.task('dev', function(cb) {
    runSequence(
        ['minify-css', 'minify-js', 'copy', 'html', 'images', 'data', 'fonts'],
        'browserSync',
        'watch',
        cb
    );
});

// Set up watches
gulp.task('watch', function() {
    gulp.watch('src/sass/**/*.scss', ['minify-css']);
    gulp.watch('src/js/**/*.js', ['minify-js']);
    gulp.watch('src/img/**/*', ['images']);
    gulp.watch('src/data/**/*', ['data']);
    gulp.watch('src/fonts/**/*', ['fonts']);
    gulp.watch('src/**/*.html', ['html']);
});


function throwError(taskName, msg) {
  throw new gutil.PluginError({
      plugin: taskName,
      message: msg
    });
}
