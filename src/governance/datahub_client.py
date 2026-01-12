import time
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.specific.dataset import DatasetPatchBuilder
import datahub.metadata.schema_classes as models
from config import Config

class DataHubGovernor:
    """
    Handles all interactions with the DataHub GMS.
    Responsible for emitting lineage, ownership, tags, and custom properties.
    """
    
    def __init__(self):
        self.emitter = DatahubRestEmitter(gms_server=Config.DATAHUB_URL, token=Config.DATAHUB_TOKEN)

    def emit_file_metadata(self, filename, target_collection, pii_details, chunk_count, system_meta=None):
        """
        Emits metadata for a processed file.
        
        Args:
            filename (str): Relative path of the source file.
            target_collection (str): Name of the destination vector index.
            pii_details (list): List of Personally Identifiable Information, findings (if any).
            chunk_count (int): Number of text chunks extracted.
            system_meta (dict): OS level metadata (size, creation time, etc.).
        """
        # Ensure URNs are cross platform compatible
        clean_filename = filename.replace("\\", "/")
        source_urn = f"urn:li:dataset:(urn:li:dataPlatform:external,file://{clean_filename},PROD)"
        vector_db_urn = f"urn:li:dataset:(urn:li:dataPlatform:pinecone,{target_collection},PROD)"

        # 1. Assigning Ownership
        self.emitter.emit(MetadataChangeProposalWrapper(
            entityUrn=vector_db_urn,
            aspect=models.OwnershipClass(
                owners=[models.OwnerClass(
                    owner="urn:li:corpuser:admin", 
                    type=models.OwnershipTypeClass.DATA_STEWARD
                )]
            )
        ))

        # 2. Patch Lineage
        # We used DatasetPatchBuilder to append upstream edges without overwriting existing lineage 
        patch_builder = DatasetPatchBuilder(vector_db_urn)
        patch_builder.add_upstream_lineage(models.UpstreamClass(
            dataset=source_urn,
            type=models.DatasetLineageTypeClass.TRANSFORMED,
            auditStamp=models.AuditStampClass(
                time=int(time.time() * 1000), 
                actor="urn:li:corpuser:ingestion-script"
            )
        ))
        
        for patch_mcp in patch_builder.build():
            self.emitter.emit(patch_mcp)

        # 3. Construct Properties & Governance Aspects
        # Initialize base operational metadata
        custom_props = {
            "quality_score": "100" if chunk_count > 0 else "0",
            "chunk_count": str(chunk_count)
        }

        # Merge system metadata (Size, Date, Extension) if available
        if system_meta:
            custom_props.update(system_meta)

        # Handle PII/Governance specific logic
        if pii_details:
            custom_props.update({
                "pii_detected": "True",
                "risk_level": "HIGH",
                "pii_audit_log": " | ".join(pii_details[:10])
            })
            
            self.emitter.emit(MetadataChangeProposalWrapper(
                entityUrn=source_urn,
                aspect=models.GlossaryTermsClass(
                    terms=[models.GlossaryTermAssociationClass(urn="urn:li:glossaryTerm:Classification.Sensitive")],
                    auditStamp=models.AuditStampClass(time=int(time.time() * 1000), actor="urn:li:corpuser:admin")
                )
            ))
            
            # Tag destination index as containing PII
            self.emitter.emit(MetadataChangeProposalWrapper(
                entityUrn=vector_db_urn,
                aspect=models.GlobalTagsClass(tags=[models.TagAssociationClass(tag="urn:li:tag:PII")])
            ))
        else:
            custom_props.update({
                "pii_detected": "False",
                "risk_level": "LOW"
            })

        # Emit final properties to the source entity
        self.emitter.emit(MetadataChangeProposalWrapper(
            entityUrn=source_urn,
            aspect=models.DatasetPropertiesClass(customProperties=custom_props)
        ))