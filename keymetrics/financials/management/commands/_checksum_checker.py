from keymetrics.financials.models import Checksum, Company


def checksum_checker(current_checksum: str, company: Company, api_type: str) -> bool:
    """
    Function to check the checksum of current API call against the stored checksum (if it exists)

    :param current_checksum: MD5 Checksum of from the current API call
    :param company: Company of the API call
    :param api_type: Either Fact or Submission (F or S) SEC API type
    :return: True if current checksum matches stored checksum, False if not
    """

    try:
        checksum_qry = Checksum.objects.get(company=company, api_type=api_type)
        stored_checksum = checksum_qry.checksum
    except Checksum.DoesNotExist:
        stored_checksum = ""

    if current_checksum == stored_checksum:
        return True
    else:
        Checksum.objects.update_or_create(
            company=company,
            api_type=api_type,
            defaults={"checksum": current_checksum},
        )
        return False
