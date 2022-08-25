CHARACTER_SCHEMA = """
query ($page: Int, $perPage: Int, $search: String, $sort: [CharacterSort]) {
  Page(page: $page, perPage: $perPage) {
    characters(search: $search, sort: $sort) {
      name {
        full
        native
        alternative
      }
      image {
        large
      }
      description(asHtml: false)
      gender
      dateOfBirth {
        year
        month
        day
      }
      age
      siteUrl
      media(perPage: 10) {
        nodes {
          siteUrl
          type
          title {
            english
            romaji
          }
        }
      }
    }
  }
}
"""


GENRE_COLLECTION_SCHEMA = """
query {
  GenreCollection
}
"""


GENRE_SCHEMA = """
query ($page: Int, $perPage: Int, $genre: String, $type: MediaType, $format_in: [MediaFormat]) {
  Page(page: $page, perPage: $perPage) {
    media(genre: $genre, type: $type, format_in: $format_in) {
      id
      idMal
      title {
        romaji
        english
      }
      coverImage {
        large
        color
      }
      description
      bannerImage
      format
      status
      type
      meanScore
      startDate {
        year
        month
        day
      }
      endDate {
        year
        month
        day
      }
      duration
      source
      episodes
      chapters
      volumes
      studios {
        nodes {
          name
        }
      }
      synonyms
      genres
      trailer {
        id
        site
      }
      externalLinks {
        site
        url
      }
      siteUrl
      isAdult
      nextAiringEpisode {
        episode
        airingAt
      }
    }
  }
}
"""


MEDIA_SCHEMA = """
query ($page: Int, $perPage: Int, $search: String, $type: MediaType, $sort: [MediaSort]) {
  Page(page: $page, perPage: $perPage) {
    media(search: $search, type: $type, sort: $sort) {
      id
      idMal
      title {
        english
        native
        romaji
      }
      coverImage {
        large
        color
      }
      description
      bannerImage
      format
      status
      type
      meanScore
      startDate {
        year
        month
        day
      }
      endDate {
        year
        month
        day
      }
      duration
      source
      episodes
      chapters
      volumes
      studios {
        nodes {
          name
        }
      }
      synonyms
      genres
      trailer {
        id
        site
      }
      externalLinks {
        site
        url
      }
      siteUrl
      isAdult
      nextAiringEpisode {
        episode
        airingAt
      }
    }
  }
}
"""


SCHEDULE_SCHEMA = """
query ($page: Int, $perPage: Int, $notYetAired: Boolean, $sort: [AiringSort]) {
  Page(page: $page, perPage: $perPage) {
    airingSchedules(notYetAired: $notYetAired, sort: $sort) {
      airingAt
      episode
      media {
        duration
        format
        idMal
        isAdult
        siteUrl
        title {
          romaji
          english
        }
        coverImage {
          large
        }
        externalLinks {
          site
          url
        }
        trailer {
          id
          site
        }
      }
    }
  }
}
"""


STAFF_SCHEMA = """
query ($page: Int, $perPage: Int, $search: String) {
  Page(page: $page, perPage: $perPage) {
    staff(search: $search, sort: FAVOURITES_DESC) {
      name {
        full
        native
        alternative
      }
      age
      description(asHtml: false)
      gender
      homeTown
      primaryOccupations
      siteUrl
      yearsActive
      dateOfBirth {
        year
        month
        day
      }
      dateOfDeath {
        year
        month
        day
      }
      image {
        large
      }
      staffMedia(perPage: 40, sort: TRENDING_DESC) {
        nodes {
          format
          siteUrl
          status
          title {
            english
            romaji
          }
        }
      }
      characters(perPage: 40, sort: FAVOURITES_DESC) {
        nodes {
          siteUrl
          name {
            full
            native
            alternative
          }
        }
      }
    }
  }
}
"""


STUDIO_SCHEMA = """
query ($page: Int, $perPage: Int, $search: String) {
  Page(page: $page, perPage: $perPage) {
    studios(search: $search) {
      name
      favourites
      isAnimationStudio
      siteUrl
      media(sort: POPULARITY_DESC, perPage: 30) {
        nodes {
          episodes
          format
          isAdult
          siteUrl
          status
          title {
            english
            romaji
          }
        }
      }
    }
  }
}
"""


TAG_COLLECTION_SCHEMA = """
query {
  MediaTagCollection {
    name
    description
    isAdult
  }
}
"""


TAG_SCHEMA = """
query ($page: Int, $perPage: Int, $tag: String, $type: MediaType, $format_in: [MediaFormat]) {
  Page(page: $page, perPage: $perPage) {
    media(tag: $tag, type: $type, format_in: $format_in) {
      id
      idMal
      title {
        romaji
        english
      }
      coverImage {
        large
        color
      }
      description
      bannerImage
      format
      status
      type
      meanScore
      startDate {
        year
        month
        day
      }
      endDate {
        year
        month
        day
      }
      duration
      source
      episodes
      chapters
      volumes
      studios {
        nodes {
          name
        }
      }
      synonyms
      genres
      trailer {
        id
        site
      }
      externalLinks {
        site
        url
      }
      siteUrl
      isAdult
      nextAiringEpisode {
        episode
        airingAt
      }
    }
  }
}
"""


USER_SCHEMA = """
query ($page: Int, $perPage: Int, $search: String) {
  Page(page: $page, perPage: $perPage) {
    users(search: $search) {
      id
      name
      about(asHtml: false)
      avatar {
        large
      }
      bannerImage
      siteUrl
      previousNames {
        name
        createdAt
        updatedAt
      }
      statistics {
        anime {
          count
          meanScore
          minutesWatched
          episodesWatched
        }
        manga {
          count
          meanScore
          chaptersRead
          volumesRead
        }
      }
    }
  }
}
"""
