import wave
import math
import copy
import numpy as np


class AudioEditor:
    def __init__(self, file_name):
        self.file_name = file_name
        self.frames = None

        self.nchannels = None
        self.sampwidth = None
        self.framerate = None
        self.nframes = None
        self.comptype = None
        self.compname = None
        self.peak = None
        self.content = b''
        self.types = None
        self.set_parameters(file_name)

    def set_parameters(self, file_name):
        wav = wave.open(file_name, mode="rb")
        params = wav.getparams()
        self.frames = self.get_frames(wav)
        wav.setpos(0)
        self.content = wav.readframes(wav.getnframes())
        wav.close()
        self.set_wav_params(params)
        self.peak = 256 ** self.sampwidth / 2
        self.types = {
            1: np.int8,
            2: np.int16,
            4: np.int32
        }

    def get_frames(self, file):
        frames = []
        frame = file.readframes(1)
        while frame != b'':
            frames.append(frame)
            frame = file.readframes(1)
        return frames

    def set_wav_params(self, params):
        self.nchannels = params.nchannels
        self.nframes = params.nframes
        self.sampwidth = params.sampwidth
        self.framerate = params.framerate
        self.comptype = params.comptype
        self.compname = params.compname

    def add_channels_into_frames(self, count_of_channels):
        self.nchannels += count_of_channels
        while count_of_channels > 0:
            new_frames = []
            for frame in self.frames:
                new_frame = frame + frame * (self.nchannels - 1)
                new_frames.append(new_frame)
            self.frames = new_frames
            count_of_channels -= 1

    def extend_samples(self, sampwidth):
        new_frames = []
        self.sampwidth += sampwidth
        for frame in self.frames:
            new_frames.append(frame + b'\xff' * sampwidth)
        self.frames = new_frames

    def add_channels_and_extend_samples(self, other_audio):
        if self.nchannels != max(self.nchannels, other_audio.nchannels):
            difference_nchannels = max(self.nchannels, other_audio.nchannels) - self.nchannels
            self.add_channels_into_frames(difference_nchannels)
        if self.sampwidth != max(self.sampwidth, other_audio.sampwidth):
            difference_sampwidth = max(self.sampwidth, other_audio.sampwidth) - self.sampwidth
            self.extend_samples(difference_sampwidth)

    def join(self, other_audio):
        other_audio = AudioEditor(other_audio)
        self.add_channels_and_extend_samples(other_audio)
        copy_other_audio = copy.deepcopy(other_audio)
        copy_other_audio.add_channels_and_extend_samples(self)
        self.frames += copy_other_audio.frames
        self.nframes = len(self.frames)

    def split_and_write_result_in_new_files(self, position_in_milliseconds):
        if position_in_milliseconds == 0:
            return
        new_frames = self.split_and_get_two_frames(position_in_milliseconds)
        self.write_changes_to_two_new_file(new_frames)

    def split_and_get_two_frames(self, position_in_milliseconds):
        new_frames = []
        frames = []
        for i in range(len(self.frames)):
            if (i / self.framerate) * 1000 == position_in_milliseconds:
                new_frames.append(frames)
                frames = []
            frames.append(self.frames[i])
        new_frames.append(frames)
        return new_frames

    def write_changes_to_two_new_file(self, new_frames):
        file_names = ['first_splitting_' + self.file_name, 'second_splitting_' + self.file_name]
        for i in range(len(new_frames)):
            frames = b''.join(new_frames[i])
            new_file = wave.open(file_names[i], mode="wb")
            self.set_params_for_new_file_for_split(new_file, len(new_frames[i]))
            new_file.writeframes(frames)
            new_file.close()

    def set_params_for_new_file_for_split(self, new_file, nframe):
        new_file.setcomptype(self.comptype, self.compname)
        new_file.setframerate(self.framerate)
        new_file.setnchannels(self.nchannels)
        new_file.setsampwidth(self.sampwidth)
        new_file.setnframes(nframe)

    def get_separated_frame_in_samples(self, frame):
        samples = []
        start_channel = 0
        for channel in range(self.nchannels):
            end_channel = int(len(frame) / self.nchannels) * (channel + 1)
            samples.append(frame[start_channel:end_channel])
            start_channel = end_channel
            end_channel *= channel + 1
        return samples

    def sample_to_int(self, sample):
        return np.fromstring(sample, dtype=self.types[self.sampwidth])

    def calculate_dB_and_sign(self, sample_converted_to_int, dB, sign):
        if sample_converted_to_int == 0:
            dB.append(0)
            sign.append(0)
        else:
            dB.append(20 * math.log10(abs(sample_converted_to_int) / self.peak))
            sign.append(math.copysign(1, sample_converted_to_int))

    def get_new_sample_value(self, dB_value, sign_value):
        n = self.peak * (10 ** (dB_value / 20)) * sign_value
        if abs(int(n)) > self.peak:
            if sign_value == 1:
                n = self.peak - 1
            else:
                n = -self.peak
        return n

    def int_to_bytes(self, value):
        if self.sampwidth == 1:
            return int(value).to_bytes(self.sampwidth, byteorder='little', signed=False)
        return int(value).to_bytes(self.sampwidth, byteorder='little', signed=True)

    def content_to_int_and_get_converted_channels_of_samples(self):
        converted_channel = []
        samples = np.fromstring(self.content, dtype=self.types[self.sampwidth])
        for n in range(self.nchannels):
            converted_channel.append(samples[n::self.nchannels])
        return converted_channel

    def change_temp_for_each_channel_and_get_samples(self, factor, window_size, h):
        converted_channels_of_samples = self.content_to_int_and_get_converted_channels_of_samples()
        new_converted_channels = []
        for converted_sample in converted_channels_of_samples:
            new_converted_channels.append(self.change_temp_for_one_channel_and_get_samples(converted_sample,
                                                                                           factor, window_size, h))
        return new_converted_channels

    def channels_to_bytes(self, channels_in_int):
        new_bytes_channels = []
        for k in range(len(channels_in_int)):
            new_bytes_channels.append([])
            for sample in channels_in_int[k]:
                new_bytes_channels[k].append(self.int_to_bytes(sample))
        return new_bytes_channels

    def get_different_channels_to_frames(self, new_bytes_channels):
        new_frames = []
        for i in range(len(new_bytes_channels[0])):
            sample = b''
            for j in range(len(new_bytes_channels)):
                sample += new_bytes_channels[j][i]
            new_frames.append(sample)
        return new_frames

    def change_temp(self, factor, window_size=2**13, h=2**11):
        if factor == 1:
            return
        new_converted_channels = self.change_temp_for_each_channel_and_get_samples(factor, window_size, h)
        new_bytes_channels = self.channels_to_bytes(new_converted_channels)
        self.frames = self.get_different_channels_to_frames(new_bytes_channels)
        self.nframes = len(self.frames)

    def change_pitch(self, pitch_in_semitone, window_size=2 ** 13, h=2 ** 11):
        if pitch_in_semitone < -12 or pitch_in_semitone > 12:
            return
        factor = 2 ** (1.0 * pitch_in_semitone / 12.0)
        self.change_temp(1.0 / factor, window_size, h)
        self.frames = self.frames[window_size:]
        self.change_speed(factor)

    def get_spectra_of_windows(self, content, start, end, hanning_window):
        part_of_content = content[int(start):int(end)]
        return np.fft.fft(hanning_window * part_of_content)

    def change_temp_for_one_channel_and_get_samples(self, content, factor, window_size, h):
        phase = np.zeros(window_size)
        hanning_window = np.hanning(window_size)
        result = np.zeros(int(len(content) / factor) + window_size)

        for i in np.arange(0, len(content) - (window_size + h), h * factor):
            first_spectra, second_spectra = self.get_spectra_of_two_consecutive_windows(content, h, i,
                                                                                        window_size, hanning_window)
            phase = self.get_rephased_all_frequencies(first_spectra, phase, second_spectra)
            second_spectra_rephased = np.fft.ifft(np.abs(second_spectra) * np.exp(1j * phase))
            i2 = int(i / factor)
            result[i2: i2 + window_size] += hanning_window * second_spectra_rephased.real

        result = ((2 ** (16 - 4)) * result / result.max())
        return result

    def get_rephased_all_frequencies(self, first_spectra, phase, second_spectra):
        phase = (phase + np.angle(second_spectra) - np.angle(first_spectra)) % 2 * np.pi
        return phase

    def get_spectra_of_two_consecutive_windows(self, content, h, i, window_size, hanning_window):
        first_spectra = self.get_spectra_of_windows(content, i, i + window_size, hanning_window)
        second_spectra = self.get_spectra_of_windows(content, i + h, i + window_size + h, hanning_window)
        return first_spectra, second_spectra

    def change_volume(self, volume_in_dB):
        if volume_in_dB == 0:
            return
        new_frames = []
        for frame in self.frames:
            new_frame = self.change_volume_for_one_frame(frame, volume_in_dB)
            new_frames.append(new_frame)
        self.frames = new_frames

    def change_volume_for_one_frame(self, frame, volume_in_dB):
        new_frame = b''
        dB = []
        sign = []
        samples = self.get_separated_frame_in_samples(frame)
        for sample in samples:
            sample_converted_to_int = self.sample_to_int(sample)
            self.calculate_dB_and_sign(sample_converted_to_int, dB, sign)
        for i in range(len(dB)):
            if dB[i] != 0:
                dB[i] += volume_in_dB
        for i in range(len(dB)):
            new_sample_converted_in_int = self.get_new_sample_value(dB[i], sign[i])
            new_frame += self.int_to_bytes(new_sample_converted_in_int)
        return new_frame

    def change_speed(self, factor):
        if factor == 1:
            return
        future_count_of_frames = round(len(self.frames) / factor)
        count_of_groups = abs(len(self.frames) - future_count_of_frames)
        count_of_frames_in_groups = round(len(self.frames) / count_of_groups)
        new_frames = []
        i = 1
        for frame in self.frames:
            if i % count_of_frames_in_groups == 0:
                if factor > 1:
                    i += 1
                    continue
                else:
                    new_frames.append(frame)
            new_frames.append(frame)
            i += 1
        self.frames = new_frames
        self.nframes = len(new_frames)

    def write_changes_to_new_file(self):
        new_name = 'changing_' + self.file_name
        frames = b''.join(self.frames)
        new_file = wave.open(new_name, mode="wb")
        self.set_params_for_new_file(new_file)
        new_file.writeframes(frames)
        new_file.close()

    def set_params_for_new_file(self, new_file):
        new_file.setcomptype(self.comptype, self.compname)
        new_file.setframerate(self.framerate)
        new_file.setnchannels(self.nchannels)
        new_file.setsampwidth(self.sampwidth)
        new_file.setnframes(self.nframes)
