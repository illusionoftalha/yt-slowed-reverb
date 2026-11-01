import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from scipy.signal import fftconvolve
import slowed_reverb as audio


class AudioFastPathTests(unittest.TestCase):
    def test_dry_reverb_skips_ir_and_convolution(self):
        for shape in [(100,), (100, 2)]:
            samples = np.ones(shape, dtype=np.float32)
            with patch.object(audio, 'make_reverb_ir') as make_ir, patch.object(audio, 'fftconvolve') as convolve:
                self.assertIs(audio.apply_reverb(samples, 8000, 0, 2.5), samples)
            make_ir.assert_not_called()
            convolve.assert_not_called()

    def test_enabled_reverb_matches_existing_mix(self):
        rng = np.random.default_rng(42)
        ir = rng.normal(size=20).astype(np.float32)
        for shape in [(100,), (100, 2)]:
            samples = rng.normal(size=shape).astype(np.float32)
            if samples.ndim == 2:
                wet = np.stack([fftconvolve(samples[:, c], ir)[:len(samples)] for c in range(2)], axis=1)
            else:
                wet = fftconvolve(samples, ir)[:len(samples)]
            wet *= (np.sqrt(np.mean(samples ** 2)) + 1e-8) / (np.sqrt(np.mean(wet ** 2)) + 1e-8)
            with patch.object(audio, 'make_reverb_ir', return_value=ir):
                actual = audio.apply_reverb(samples, 8000, 0.4, 2.5)
            np.testing.assert_allclose(actual, 0.6 * samples + 0.4 * wet, atol=1e-6)

    def test_neutral_effects_preserve_mono_and_stereo_samples(self):
        for shape in [(100,), (2, 100)]:
            samples = np.linspace(-0.5, 0.5, np.prod(shape), dtype=np.float32).reshape(shape)
            with tempfile.TemporaryDirectory() as directory, \
                    patch('builtins.print'), patch.object(audio, 'librosa') as librosa, \
                    patch.object(audio.sf, 'write') as write, patch.object(audio.os.path, 'getsize', return_value=0):
                librosa.load.return_value = (samples, 8000)
                audio.process_audio('input.wav', str(Path(directory) / 'out.wav'),
                                    speed=1.0, pitch=0, reverb_wet=0, bass_boost=0)
            librosa.effects.time_stretch.assert_not_called()
            np.testing.assert_array_equal(write.call_args.args[1], samples.T)


if __name__ == '__main__':
    unittest.main()
