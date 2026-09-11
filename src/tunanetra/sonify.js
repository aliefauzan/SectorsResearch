/*
 * Sonification for two things, and nothing else.
 *
 * Fu 2026 measured audio against a visual baseline for stock-chart tasks and found
 * parity in two places — trend direction and discrete event detection — and a real gap
 * in two others: volatility judgements, which rely on perceiving band width, and tasks
 * needing concurrent integration of several indicators. So this file plays a series
 * direction and it plays an event, and every other number on the page is spoken instead.
 * `narrate.check_audio_zone` is the gate that keeps a later change from routing a
 * comparison in here.
 *
 * VoxLens found the residual interaction-time gap comes from large cardinality — hearing
 * a long series takes time no matter how well it is mapped. The summary is therefore
 * always on the page before this ever runs, audio is off by default, and the longest
 * series it will play is the 62-point foreign-flow window.
 *
 * No library. There is no mature sonification package for price series — the ones that
 * exist are astronomy tools, and VoxLens says the same thing about its own field — so
 * this is ~120 lines of Web Audio and that is the whole dependency footprint.
 */
(function () {
  "use strict";

  var context = null;

  function audio() {
    if (!context) {
      var Ctor = window.AudioContext || window.webkitAudioContext;
      if (!Ctor) return null;
      context = new Ctor();
    }
    // Browsers suspend the context until a gesture. Every entry point here is a click
    // or a key, so resuming is always legitimate.
    if (context.state === "suspended") context.resume();
    return context;
  }

  // Map a value onto a pitch inside one octave and a half. Wider ranges sound dramatic
  // and read as noise; this range keeps the direction audible without implying
  // precision the mapping does not have.
  var LOW_HZ = 220;
  var HIGH_HZ = 660;

  function toPitch(value, min, max) {
    if (max === min) return (LOW_HZ + HIGH_HZ) / 2;
    var t = (value - min) / (max - min);
    return LOW_HZ * Math.pow(HIGH_HZ / LOW_HZ, t);
  }

  /*
   * Play a series as a pitch sweep. Long series are decimated rather than played in
   * full: 62 points at 90 ms is 5.6 seconds, which is already at the edge of what a
   * listener will sit through to learn one direction.
   */
  function playSeries(values, options) {
    var ctx = audio();
    if (!ctx || !values || values.length < 2) return 0;
    options = options || {};
    var maxNotes = options.maxNotes || 40;
    var step = Math.max(1, Math.ceil(values.length / maxNotes));
    var notes = [];
    for (var i = 0; i < values.length; i += step) notes.push(values[i]);
    if (notes[notes.length - 1] !== values[values.length - 1]) {
      notes.push(values[values.length - 1]);   // the endpoint is the point
    }

    var min = Math.min.apply(null, notes);
    var max = Math.max.apply(null, notes);
    var noteMs = options.noteMs || 90;
    var gain = ctx.createGain();
    gain.gain.value = 0.0001;
    gain.connect(ctx.destination);

    var osc = ctx.createOscillator();
    osc.type = "sine";
    var start = ctx.currentTime + 0.02;
    osc.frequency.setValueAtTime(toPitch(notes[0], min, max), start);
    for (var n = 1; n < notes.length; n++) {
      // Stepped, not glided: a listener counts steps and hears the shape. A continuous
      // glide sounds smoother and carries less.
      osc.frequency.setValueAtTime(toPitch(notes[n], min, max),
                                   start + (n * noteMs) / 1000);
    }
    var total = (notes.length * noteMs) / 1000;
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(0.18, start + 0.03);
    gain.gain.setValueAtTime(0.18, start + total - 0.05);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + total);
    osc.connect(gain);
    osc.start(start);
    osc.stop(start + total + 0.05);
    return total;
  }

  /*
   * A discrete event. High-contrast and symmetric, per Fu 2026 — two short square-wave
   * blips at a fixed pitch, so an event never sounds like part of the trend sweep.
   */
  function playEarcon(direction) {
    var ctx = audio();
    if (!ctx) return 0;
    var hz = direction === "down" ? 340 : 880;
    var start = ctx.currentTime + 0.02;
    for (var i = 0; i < 2; i++) {
      var osc = ctx.createOscillator();
      var gain = ctx.createGain();
      osc.type = "square";
      osc.frequency.value = hz;
      gain.gain.value = 0.0001;
      var at = start + i * 0.14;
      gain.gain.exponentialRampToValueAtTime(0.12, at + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.0001, at + 0.09);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(at);
      osc.stop(at + 0.1);
    }
    return 0.25;
  }

  function stop() {
    if (context) {
      context.close();
      context = null;
    }
  }

  // Wire every button that declares a series. The series is rendered into the page as a
  // data attribute by webapp.py, so the audio plays exactly the numbers the table shows.
  function wire(root) {
    var buttons = (root || document).querySelectorAll("[data-series]");
    Array.prototype.forEach.call(buttons, function (button) {
      button.addEventListener("click", function () {
        var status = document.getElementById(button.getAttribute("aria-controls"));
        var values;
        try {
          values = JSON.parse(button.getAttribute("data-series"));
        } catch (error) {
          return;
        }
        var seconds = playSeries(values, {});
        if (status) {
          // Announced, not just played: a listener who cannot hear the tone (no audio
          // device, muted tab) still learns that something was meant to happen, and how
          // long it lasts.
          status.textContent = "Memutar " + values.length + " titik, sekitar " +
            seconds.toFixed(1) + " detik. Angka lengkapnya ada di tabel di bawah.";
        }
      });
    });
  }

  window.Sonify = { playSeries: playSeries, playEarcon: playEarcon, stop: stop,
                    wire: wire };
  if (document.readyState !== "loading") wire(document);
  else document.addEventListener("DOMContentLoaded", function () { wire(document); });
})();
