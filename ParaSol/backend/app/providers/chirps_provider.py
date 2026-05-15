import ee

def get_chirps_collection(start_date, end_date):

    return (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterDate(start_date, end_date)
    )