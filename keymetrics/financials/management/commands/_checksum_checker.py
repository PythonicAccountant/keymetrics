from keymetrics.financials.models import Checksum, Company


def checksum_checker(current_checksum: str, company: Company, api_type: str) -> bool:
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
