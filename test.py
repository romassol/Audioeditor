from unittest import TestCase, main
import numpy as np
import copy
from audioeditor import AudioEditor


class TestAudioEditor(TestCase):

    def test_add_channels_into_frames(self):
        s = AudioEditor('bowl.wav')
        self.assertEqual(1, s.nchannels)
        old_frames = s.frames
        s.add_channels_into_frames(1)
        self.assertEqual(2, s.nchannels)
        for i in range(len(s.frames)):
            frame = s.frames[i]
            self.assertEqual(old_frames[i], frame[:int(len(frame)/2)], frame[int(len(frame)/2):])

    def test_extend_samples(self):
        s = AudioEditor('bowl.wav')
        self.assertEqual(2, s.sampwidth)
        old_frames = s.frames
        old_sampwidth = s.sampwidth
        s.extend_samples(1)
        self.assertEqual(3, s.sampwidth)
        for i in range(len(s.frames)):
            self.assertEqual(3, len(s.frames[i]))
            difference = s.sampwidth - old_sampwidth
            self.assertEqual(old_frames[i] + b'\xff'*difference, s.frames[i])

    def test_get_separated_frame_in_samples(self):
        s1 = AudioEditor('bowl.wav')
        for frame in s1.frames:
            samples = s1.get_separated_frame_in_samples(frame)
            self.assertEqual([frame], samples)
        s2 = AudioEditor('обычный.wav')
        for frame in s2.frames:
            samples = s2.get_separated_frame_in_samples(frame)
            self.assertEqual([frame[:int(len(frame)/2)], frame[int(len(frame)/2):]], samples)

    def test_add_channels_and_extend_samples(self):
        s1 = AudioEditor('обр.wav')
        s2 = AudioEditor('bowl.wav')
        s2.add_channels_and_extend_samples(s1)
        self.assertEqual(2, s2.sampwidth)
        self.assertEqual(2, s2.nchannels)

        s1 = AudioEditor('обр.wav')
        s2 = AudioEditor('bowl.wav')
        s1.add_channels_and_extend_samples(s2)
        self.assertEqual(2, s1.sampwidth)
        self.assertEqual(2, s1.nchannels)

    def test_join(self):
        s1 = AudioEditor('обр.wav')
        s2 = AudioEditor('обычный.wav')
        old_nframes_s1 = s1.nframes
        old_nframes_s2 = s2.nframes
        old_frames_s1 = copy.deepcopy(s1.frames)
        s1.join('обычный.wav')

        self.assertEqual(2, s2.sampwidth)
        self.assertEqual(2, s2.nchannels)
        self.assertEqual(old_nframes_s2, s2.nframes)

        self.assertEqual(2, s1.sampwidth)
        self.assertEqual(2, s1.nchannels)
        self.assertEqual(old_nframes_s1 + old_nframes_s2, s1.nframes)
        self.assertEqual(old_frames_s1, s1.frames[:old_nframes_s1])
        self.assertEqual(s2.frames, s1.frames[old_nframes_s1:])

    def test_split_and_get_two_frames(self):
        s = AudioEditor('обычный.wav')
        frames = s.split_and_get_two_frames(3000)
        self.assertEqual(frames[0] + frames[1], s.frames)
        self.assertEqual(len(frames[0]) + len(frames[1]), len(s.frames))

    def test_write_changes_to_two_new_file(self):
        s = AudioEditor('обычный.wav')
        frames = s.split_and_get_two_frames(6000)
        s.write_changes_to_two_new_file(frames)
        s1 = AudioEditor('first_splitting_обычный.wav')
        s2 = AudioEditor('second_splitting_обычный.wav')
        self.assertEqual(s.sampwidth, s1.sampwidth, s2.sampwidth)
        self.assertEqual(frames[0], s1.frames)
        self.assertEqual(len(frames[0]), len(s1.frames))
        self.assertEqual(frames[1], s2.frames)
        self.assertEqual(len(frames[1]), len(s2.frames))
        self.assertEqual(s.comptype, s1.comptype, s2.comptype)
        self.assertEqual(s.compname, s1.compname, s2.compname)
        self.assertEqual(s.framerate, s1.framerate, s2.framerate)
        self.assertEqual(s.nchannels, s1.nchannels, s2.nchannels)

    def test_calculate_dB_and_sign(self):
        s = AudioEditor('обычный.wav')
        sample_converted_to_int = 0
        sign = []
        dB = []
        s.calculate_dB_and_sign(sample_converted_to_int, dB, sign)
        self.assertEqual(1, len(dB))
        self.assertEqual(0, dB[0])
        self.assertEqual(1, len(sign))
        self.assertEqual(0, sign[0])

        sample_converted_to_int = -s.peak * 10
        sign = []
        dB = []
        s.calculate_dB_and_sign(sample_converted_to_int, dB, sign)
        self.assertEqual(1, len(dB))
        self.assertEqual(20, dB[0])
        self.assertEqual(1, len(sign))
        self.assertEqual(-1, sign[0])

    def test_get_new_sample_value(self):
        s = AudioEditor('обычный.wav')

        dB_value = 20
        sign_value = 1
        n = s.get_new_sample_value(dB_value, sign_value)
        self.assertEqual(s.peak - 1, n)

        sign_value = -1
        n = s.get_new_sample_value(dB_value, sign_value)
        self.assertEqual(-s.peak , n)

        dB_value = -6
        sign_value = 1
        n = s.get_new_sample_value(dB_value, sign_value)
        self.assertEqual(16423, round(n))

    def test_content_to_int_and_get_converted_channels_of_samples(self):
        s = AudioEditor('обычный.wav')
        converted_channels_of_samples = s.content_to_int_and_get_converted_channels_of_samples()
        self.assertEqual(s.nchannels, len(converted_channels_of_samples))

    def test_channels_to_bytes(self):
        s = AudioEditor('обычный.wav')
        channels = [[1, 2, 3, 4], [5, 6, 7, 8]]
        self.assertEqual([[b'\x01\x00', b'\x02\x00', b'\x03\x00', b'\x04\x00'],
                          [b'\x05\x00', b'\x06\x00', b'\x07\x00', b'\x08\x00']], s.channels_to_bytes(channels))

    def test_get_different_channels_to_frames(self):
        s = AudioEditor('обычный.wav')
        channels = [[b'\x01\x00', b'\x02\x00', b'\x03\x00', b'\x04\x00'],
                    [b'\x05\x00', b'\x06\x00', b'\x07\x00', b'\x08\x00']]
        self.assertEqual([b'\x01\x00\x05\x00', b'\x02\x00\x06\x00', b'\x03\x00\x07\x00', b'\x04\x00\x08\x00'],
                         s.get_different_channels_to_frames(channels))

    def test_change_volume_for_one_frame(self):
        s = AudioEditor('обычный.wav')
        avs = AudioEditor('усиленный на 10.wav')
        s.change_volume_for_one_frame(s.frames[0], 10)
        self.assertEqual(len(avs.frames), len(s.frames))
        n1 = int.from_bytes(avs.frames[0], byteorder='big', signed=True)
        n2 = int.from_bytes(s.frames[0], byteorder='big', signed=True)
        self.assertAlmostEqual(n1, n2, delta=1000)

    def test_change_speed(self):
        s = AudioEditor('обычный.wav')
        old_nframes = s.nframes
        old_frames = copy.deepcopy(s.frames)
        s.change_speed(2)
        self.assertEqual(round(old_nframes / 2), len(s.frames))
        self.assertEqual([old_frames[i] for i in range(len(old_frames)) if i % 2 == 0], s.frames)


if __name__ == '__main__':
    main()
