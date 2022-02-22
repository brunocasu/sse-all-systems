from sklearn.preprocessing import LabelEncoder


class DataframeEncoding:

    def encode(self, dataframe):
        encoder = {
            "1": {"sport": 0, "meditation": 1},
            "2": {"pop-music": 0, "ambient-music": 1},
            "3": {"focused": 0, "relaxed": 1, "excited": 2, "stressed": 3}
        }

        dataframe = dataframe.replace(encoder)
        return dataframe
