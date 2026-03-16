import tator

from application.tator.tator_base_qaqc_processor import TatorBaseQaqcProcessor


class TatorSubQaqcProcessor(TatorBaseQaqcProcessor):
    def __init__(
            self,
            project_id: int,
            section_ids: list[str],
            api: tator.api,
            tator_url: str,
            darc_review_url: str = None,
            transect_media_ids: list[int] = None,
    ):
        super().__init__(
            project_id=project_id,
            section_ids=section_ids,
            api=api,
            darc_review_url=darc_review_url,
            tator_url=tator_url,
            transect_media_ids=transect_media_ids,
        )

    def get_summary(self):
        pass

    def download_image_guide(self):
        pass