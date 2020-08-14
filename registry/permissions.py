from rest_framework.permissions import IsAuthenticated, SAFE_METHODS


class StudyPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True
        return request.user == obj.owner


class AssayPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True
        return request.user == obj.study.owner


class SamplePermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True
        return request.user == obj.assay.study.owner


class DnaPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True
        else:
            for vector in obj.vectors.all():
                for sample in vector.sample_set.all():
                    if request.user != sample.assay.study.owner:
                        return False
            return True


class MediaPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True
        else:
            for sample in obj.sample_set.all():
                if request.user != sample.assay.study.owner:
                    return False
            return True


class StrainPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True
        else:
            for sample in obj.sample_set.all():
                if request.user != sample.assay.study.owner:
                    return False
            return True


class ChemicalPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            True
        else:
            for supp in obj.supplement_set.all():
                for sample in supp.samples.all():
                    if request.user != sample.assay.study.owner:
                        return False
        return False


class SupplementPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True
        else:
            for sample in obj.samples.all():
                if request.user != sample.assay.study.owner:
                    return False
            return True


class VectorPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True
        else:
            for sample in obj.sample_set.all():
                if request.user != sample.assay.study.owner:
                    return False
            return True


class MeasurementPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True
        else:
            return request.user == obj.sample.assay.study.owner