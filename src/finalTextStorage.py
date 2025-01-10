class finalTextStorage():

    def __init__(self):
        self.final_media = {} # Either multiple versions or a single will be contained in this dictionary

    def __repr__(self):
        """ For printing contents of the finalTextStorage object """
        if self.final_media == dict():
            return "None"
        else:
            return str(self.final_media)

    def set_version(self, language, finalized_media, seo_rating, is_original=False):
        """ Sets a version of the finalized media, specifying the language """
        self.final_media[language] = {
            'finalized_version': finalized_media,
            'seo_rating': seo_rating,
            'is_original': is_original,
        }
    
    def update_text(self, language, finalized_media):
        if language not in self.final_media:
            raise ValueError("Language version not present, the following language versions are set: ", list(self.final_media.keys()))
        else:
            self.final_media[language]['finalized_version'] = finalized_media

    def update_seo_rating(self, language, seo_rating=None):
        if language not in self.final_media:
            raise ValueError("Language version not present, the following language versions are set: ", list(self.final_media.keys()))
        else:
            self.final_media[language]['seo_rating'] = seo_rating # This will set to None if not specified, this is for the case where the current finalized version didn't have an seo analysis run on it

    def get_seo_rating(self, language):
        """ Allows user to retrieve the version of the media in the specified language """
        return self.final_media[language]['seo_rating']
    
    def get_text(self, language):
        """ Allows user to retrieve the version of the media in the specified language """
        return self.final_media[language]['finalized_version']