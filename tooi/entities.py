"""
Dataclasses which represent entities returned by the Mastodon API.
"""

from dataclasses import dataclass
from datetime import date, datetime
from functools import cached_property
from html2text import html2text
from typing import Optional, Type, TypeVar

from httpx import Response

from tooi.utils.from_dict import from_dict


@dataclass
class AccountField:
    """
    https://docs.joinmastodon.org/entities/Account/#Field
    """
    name: str
    value: str
    verified_at: Optional[datetime]

    @cached_property
    def value_md(self) -> str:
        return html2text(self.value, bodywidth=0)


@dataclass
class CustomEmoji:
    """
    https://docs.joinmastodon.org/entities/CustomEmoji/
    """
    shortcode: str
    url: str
    static_url: str
    visible_in_picker: bool
    category: str


@dataclass
class Account:
    """
    https://docs.joinmastodon.org/entities/Account/
    """
    id: str
    username: str
    acct: str
    url: str
    display_name: str
    note: str
    avatar: str
    avatar_static: str
    header: str
    header_static: str
    locked: bool
    fields: list[AccountField]
    emojis: list[CustomEmoji]
    bot: bool
    group: bool
    discoverable: Optional[bool]
    noindex: Optional[bool]
    moved: Optional["Account"]
    suspended: Optional[bool]
    limited: Optional[bool]
    created_at: datetime
    last_status_at: Optional[date]
    statuses_count: int
    followers_count: int
    following_count: int

    @cached_property
    def note_md(self) -> str:
        return html2text(self.note, bodywidth=0)


@dataclass
class Application:
    """
    https://docs.joinmastodon.org/entities/Status/#application
    """
    name: str
    website: Optional[str]


@dataclass
class MediaAttachment:
    """
    https://docs.joinmastodon.org/entities/MediaAttachment/
    """
    id: str
    type: str
    url: str
    preview_url: str
    remote_url: Optional[str]
    meta: dict
    description: str
    blurhash: str


@dataclass
class StatusMention:
    """
    https://docs.joinmastodon.org/entities/Status/#Mention
    """
    id: str
    username: str
    url: str
    acct: str


@dataclass
class StatusTag:
    """
    https://docs.joinmastodon.org/entities/Status/#Tag
    """
    name: str
    url: str


@dataclass
class PollOption:
    """
    https://docs.joinmastodon.org/entities/Poll/#Option
    """
    title: str
    votes_count: Optional[int]


@dataclass
class Poll:
    """
    https://docs.joinmastodon.org/entities/Poll/
    """
    id: str
    expires_at: Optional[datetime]
    expired: bool
    multiple: bool
    votes_count: int
    voters_count: Optional[int]
    options: list[PollOption]
    emojis: list[CustomEmoji]
    voted: Optional[bool]
    own_votes: Optional[list[int]]


@dataclass
class PreviewCard:
    """
    https://docs.joinmastodon.org/entities/PreviewCard/
    """
    url: str
    title: str
    description: str
    type: str
    author_name: str
    author_url: str
    provider_name: str
    provider_url: str
    html: str
    width: int
    height: int
    image: Optional[str]
    embed_url: str
    blurhash: Optional[str]

    @cached_property
    def markdown(self) -> str:
        return html2text(self.html, bodywidth=0)


@dataclass
class FilterKeyword:
    """
    https://docs.joinmastodon.org/entities/FilterKeyword/
    """
    id: str
    keyword: str
    whole_word: str


@dataclass
class FilterStatus:
    """
    https://docs.joinmastodon.org/entities/FilterStatus/
    """
    id: str
    status_id: str


@dataclass
class Filter:
    """
    https://docs.joinmastodon.org/entities/Filter/
    """
    id: str
    title: str
    context: list[str]
    expires_at: Optional[datetime]
    filter_action: str
    keywords: list[FilterKeyword]
    statuses: list[FilterStatus]


@dataclass
class FilterResult:
    """
    https://docs.joinmastodon.org/entities/FilterResult/
    """
    filter: Filter
    keyword_matches: Optional[list[str]]
    status_matches: Optional[str]


@dataclass
class Status:
    """
    https://docs.joinmastodon.org/entities/Status/
    """
    id: str
    uri: str
    created_at: datetime
    account: Account
    content: str
    visibility: str
    sensitive: bool
    spoiler_text: str
    media_attachments: list[MediaAttachment]
    application: Optional[Application]
    mentions: list[StatusMention]
    tags: list[StatusTag]
    emojis: list[CustomEmoji]
    reblogs_count: int
    favourites_count: int
    replies_count: int
    url: Optional[str]
    in_reply_to_id: Optional[str]
    in_reply_to_account_id: Optional[str]
    reblog: Optional["Status"]
    poll: Optional[Poll]
    card: Optional[PreviewCard]
    language: Optional[str]
    text: Optional[str]
    edited_at: Optional[datetime]
    favourited: Optional[bool]
    reblogged: Optional[bool]
    muted: Optional[bool]
    bookmarked: Optional[bool]
    pinned: Optional[bool]
    filtered: Optional[list[FilterResult]]
    # Hometown unfederated posts
    local_only: Optional[bool]

    @property
    def original(self) -> "Status":
        return self.reblog or self

    @cached_property
    def content_md(self) -> str:
        return html2text(self.content, bodywidth=0)


@dataclass
class StatusSource:
    """
    https://docs.joinmastodon.org/entities/StatusSource/
    """
    id: str
    text: str
    spoiler_text: str


@dataclass
class Report:
    """
    https://docs.joinmastodon.org/entities/Report/
    """
    id: str
    action_taken: bool
    action_taken_at: Optional[datetime]
    category: str
    comment: str
    forwarded: bool
    created_at: datetime
    status_ids: Optional[list[str]]
    rule_ids: Optional[list[str]]
    target_account: Account


@dataclass
class Notification:
    """
    https://docs.joinmastodon.org/entities/Notification/
    """
    id: str
    type: str
    created_at: datetime
    account: Account
    status: Optional[Status]
    report: Optional[Report]


@dataclass
class InstanceUrls:
    streaming_api: str


@dataclass
class InstanceV2Urls:
    streaming: str


@dataclass
class InstanceStats:
    user_count: int
    status_count: int
    domain_count: int


@dataclass
class InstanceStatusConfiguration:
    max_characters: int
    max_media_attachments: int
    characters_reserved_per_url: int


@dataclass
class InstanceMediaAttachmentConfiguration:
    supported_mime_types: list[str]
    image_size_limit: int
    image_matrix_limit: int
    video_size_limit: int
    video_frame_rate_limit: int
    video_matrix_limit: int


@dataclass
class InstancePollConfiguration:
    max_options: int
    max_characters_per_option: int
    min_expiration: int
    max_expiration: int


@dataclass
class InstanceConfiguration:
    """
    https://docs.joinmastodon.org/entities/V1_Instance/#configuration
    """
    statuses: InstanceStatusConfiguration
    media_attachments: InstanceMediaAttachmentConfiguration
    polls: InstancePollConfiguration


@dataclass
class InstanceV2Configuration:
    """
    https://docs.joinmastodon.org/entities/Instance/#configuration
    """
    urls: InstanceV2Urls
    statuses: InstanceStatusConfiguration
    media_attachments: InstanceMediaAttachmentConfiguration
    polls: InstancePollConfiguration


@dataclass
class Rule:
    """
    https://docs.joinmastodon.org/entities/Rule/
    """
    id: str
    text: str


@dataclass
class Instance:
    """
    https://docs.joinmastodon.org/entities/V1_Instance/
    """
    uri: str
    title: str
    short_description: str
    description: str
    email: str
    version: str
    urls: InstanceUrls
    stats: InstanceStats
    thumbnail: Optional[str]
    languages: list[str]
    registrations: bool
    approval_required: bool
    invites_enabled: bool
    configuration: InstanceConfiguration
    contact_account: Optional[Account]
    rules: list[Rule]


@dataclass
class UsageUsers:
    active_month: int


@dataclass
class Usage:
    users: UsageUsers


@dataclass
class InstanceThumbnail:
    url: str
    blurhash: Optional[str]
    versions: Optional[dict]


@dataclass
class InstanceRegistrations:
    enabled: bool
    approval_required: bool
    message: Optional[str]


@dataclass
class InstanceContact:
    email: str
    account: Account


@dataclass
class InstanceV2:
    """
    https://docs.joinmastodon.org/entities/Instance/
    """
    domain: str
    title: str
    version: str
    source_url: str
    description: str
    usage: Usage
    thumbnail: InstanceThumbnail
    languages: list[str]
    configuration: InstanceV2Configuration
    registrations: InstanceRegistrations
    contact: InstanceContact
    rules: list[Rule]


@dataclass
class ExtendedDescription:
    """
    https://docs.joinmastodon.org/entities/ExtendedDescription/
    """
    updated_at: datetime
    content: str

    @cached_property
    def content_md(self) -> str:
        return html2text(self.content, bodywidth=0)


@dataclass
class TagHistory:
    """
    Usage statistics for given days (typically the past week).
    https://docs.joinmastodon.org/entities/Tag/#history
    """
    day: str
    uses: str
    accounts: str


@dataclass
class Tag:
    """
    Represents a hashtag used within the content of a status.
    https://docs.joinmastodon.org/entities/Tag/
    """
    name: str
    url: str
    history: list[TagHistory]
    following: Optional[bool]


@dataclass
class SearchResults:
    accounts: list[Account]
    hashtags: list[Tag]
    statuses: list[Status]


# Generic data class instance
T = TypeVar("T")


def from_response(cls: Type[T], response: Response) -> T:
    return from_dict(cls, response.json())
