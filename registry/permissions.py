from rest_framework.permissions import IsAuthenticated, SAFE_METHODS


class StudyPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return request.user.has_perm('view_study', obj)
        return request.user == obj.owner


class AssayPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return request.user.has_perm('view_study', obj.study)
        return False


class SamplePermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return request.user.has_perm('view_study', obj.assay.study)
        return False


class DnaPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            for assay in obj.assays.all():
                if request.user.has_perm('view_study', assay.study):
                    return True
        return False


class MediaPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            for sample in obj.sample_set.all():
                if request.user.has_perm('view_study', sample.assay.study):
                    return True
        return False


class StrainPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            for sample in obj.sample_set.all():
                if request.user.has_perm('view_study', sample.assay.study):
                    return True
        return False


class ChemicalPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            for supp in obj.supplement_set.all():
                for sample in supp.samples.all():
                    if request.user.has_perm('view_study', sample.assay.study):
                        return True
        return False


class SupplementPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            for sample in obj.samples.all():
                if request.user.has_perm('view_study', sample.assay.study):
                    return True
        return False


class VectorPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            for dna in obj.dnas.all():
                for assay in dna.assays.all():
                    if request.user.has_perm('view_study', assay.study):
                        return True
        return False


class MeasurementPermission(IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            if request.user.has_perm('view_study', obj.sample.assay.study):
                return True
        return False
